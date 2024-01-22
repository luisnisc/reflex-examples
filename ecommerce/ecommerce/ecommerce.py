"""Welcome to Reflex! This file outlines the steps to create a basic app."""
from rxconfig import config

import reflex as rx
import json
from icecream import ic
from datetime import datetime
import pandas as pd


SEARCH_LABELS = {
    "input_name": "Name",
    "input_name_delete": "Name",
    "input_qty": "Quantity",
    "input_price": "Unit Price",
}

PAGE_WIDTH = "60vw"
FULL = "100%"

FILTERS_TAG = [
    "contains",
    "does not contains",
    "is empty",
    "is not empty",
]


class Product(rx.Base):
    name: str
    quantity: int
    price: float
    created_at: str

    def __init__(self, row):
        created_at_format = datetime.now().strftime('%Y-%m-%d %H:%M')
        name = row.get("name") or row.get("input_name")
        qty = row.get("quantity") or int(row.get("input_qty"))
        price = row.get("price") or float(row.get("input_price"))
        super().__init__(
            name=name,
            quantity=qty,
            price=price,
            created_at=created_at_format,
        )

    def sum_value(self):
        return self.quantity * self.unit_price


class State(rx.State):
    """The app state."""

    input_name: str = ""
    input_name_delete: str = ""
    input_qty: int = 0
    input_price: float = 0.0

    search_input: str = ""
    invalid_inputs: dict[str, bool] = {
        "input_name": False,
        "input_qty": False,
        "input_price": False,
    }

    products: list[Product] = []

    export_path: str = ""

    def load_products(self):
        with open("products.json") as product_file:
            data = json.load(product_file)
            self.products = [Product(row) for row in data]

    def dump_products(self):
        with open('products.json', 'w') as f:
            json.dump([product.__dict__ for product in self.products], f, indent=4)
            
    @rx.var
    def product_data(self) -> list[list]:
        return [
            [p.name, p.quantity, f"{p.price}€", p.created_at]
            for p in self.products
            if self.search_input.lower() in p.name.lower()
        ]

    def add_product(self, form_data: dict):
        ic("add new product", form_data)
        invalid = False
        for field in form_data.keys():
            ic(
                field,
            )
            if not form_data.get(field):
                self.invalid_inputs[field] = True
                invalid = True
            else:
                try:
                    type(getattr(self, field))(form_data.get(field))
                    self.invalid_inputs[field] = False
                except:
                    self.invalid_inputs[field] = True
                    invalid = True

        if not invalid:
            self.products.append(Product(form_data))
            self.save_products()
            for field in form_data.keys():
                yield rx.set_value(field, "")

    def save_products(self):
        with open("products.json", "w") as product_file:
            data = [product.__dict__ for product in self.products]
            json.dump(data, product_file)

    def export(self):
        data = [product.__dict__ for product in self.products]
        df = pd.DataFrame(data)
        df.to_csv('products.csv', index=False)
        print("Data exported to products.csv")
    
    def delete_product(self, form_data: dict):
        ic("delete product", form_data)
        invalid = False
        for field in form_data.keys():
            ic(
                field,
            )
        if not invalid:
            for product in self.products:
                if product.name == form_data.get("input_name_delete"):
                    self.products.remove(product)
                    self.save_products()
                    for field in form_data.keys():
                        yield rx.set_value(field, "")
                    break



def inventory():
    search_bar = rx.hstack(
        rx.icon(tag="info_outline"),
        rx.heading("Products", size="md"),
        rx.spacer(),
        rx.icon(tag="search"),
        rx.input(
            placeholder="Search by name", width="20%", on_change=State.set_search_input,
            background="#edf2f7"
        ),
        
        width=FULL,
    )
    table = rx.data_table(
        columns=["Name", "Quantity", "Price", "Created date"],
        data=State.product_data,
        pagination=True,
        sort=True,
        # search=True,
    )
    return rx.vstack(search_bar, table)


def field_input(var, placeholder):
    return rx.hstack(
        rx.spacer(),
        rx.text(SEARCH_LABELS[var._var_name]),
        rx.form_control(
            rx.input(
                id=var._var_name,
                placeholder=placeholder,
                is_invalid=State.invalid_inputs[var._var_name],
            ),
            width="50%",
            is_required=True,
        ),
        width=FULL,
    )


def filters():
    ...
    return rx.fragment()


def add_item():
    return rx.vstack(
        rx.hstack(
            rx.icon(tag="add"),
            rx.heading("Add a New Product", size="md"),
            rx.spacer(),
            width=FULL,
        ),
        rx.form(
            rx.box(
                rx.vstack(
                    field_input(State.input_name, "Product Name"),
                    field_input(State.input_qty, "Product Quantity"),
                    field_input(State.input_price, "Product price (in cents)"),
                    align="right",
                ),
                padding="15px",
                border="#e2e8f0 solid 2px",
                borderRadius="10px",
                background="white"
            ),
            rx.hstack(rx.spacer(), rx.button("Add Product", type_="submit"), class_name="mt-4"),
            on_submit=State.add_product,
            width=FULL,
            
            ),
        width=FULL,
    )
def delete_item():
    return rx.vstack(
        rx.hstack(
            rx.icon(tag="delete"),
            rx.heading("Delete a Product", size="md"),
            rx.spacer(),
            width=FULL,
        ),
        rx.form(
            rx.box(
                rx.vstack(
                    field_input(State.input_name_delete, "Product Name"),
                ),
                padding="15px",
                border="#e2e8f0 solid 2px",
                borderRadius="10px",
                 background="white"
            ),
            rx.hstack(rx.spacer(), rx.button("Delete Product", type_="submit", ), class_name="mt-4"),
            on_submit=(lambda event: State.delete_product(event)),
            width=FULL,
           

        ),
        width=FULL,
        
    )


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.hstack(
            rx.heading("E-Commerce Inventory"),
            rx.vstack(
            rx.button("Export", 
                      on_click=State.export,
                      
                      ),
            class_name="mt-4",
            ),
            ),
            inventory(),
            add_item(),
            delete_item(),
            rx.spacer(),
            width=PAGE_WIDTH,
            height="100%",
        ),
        height="100vh",
        background="rgb(255,149,0) linear-gradient(0deg, rgba(255,149,0,1) 0%, rgba(255,226,0,1) 35%, rgba(255,235,0,1) 100%)",
        color=""
    )


app = rx.App()
app.add_page(index, on_load=State.load_products)
