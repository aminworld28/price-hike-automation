"""Dummy product catalogue for the fictional 'Demo Bites' chain.
type/service == "" means nothing is selected (the situation that blocks the real form)."""

def _p(i, code, name, category, price, type_="", service=""):
    return {"id": i, "code": code, "name": name, "category": category, "price": price,
            "type": type_, "service": service, "status": "Active", "deal": "No"}

PRODUCTS = [
    _p(1,  "B001", "Crispy Bucket 4 Pc",      "Bucket",   899,  "Non Veg", "Delivery"),
    _p(2,  "B002", "Crispy Bucket 6 Pc",      "Bucket",   1299),
    _p(3,  "B003", "Crispy Bucket 8 Pc",      "Bucket",   1699, "Non Veg", "All"),
    _p(4,  "G001", "Classic Chicken Burger",  "Burger",   349),
    _p(5,  "G002", "Spicy Chicken Burger",    "Burger",   379,  "Non Veg", "All"),
    _p(6,  "G003", "Veg Crunch Burger",       "Burger",   299),
    _p(7,  "G004", "Paneer Royale Burger",    "Burger",   329),
    _p(8,  "G005", "Gold Veg Burger Meal",    "Burger",   449,  "", "All"),
    _p(9,  "S001", "Chicken Strips 3 Pc",     "Snacks",   249,  "Non Veg", ""),
    _p(10, "S002", "Chicken Strips 6 Pc",     "Snacks",   449),
    _p(11, "S003", "Veg Nuggets 6 Pc",        "Snacks",   229),
    _p(12, "S004", "Non Veg Platter",         "Snacks",   549),
    _p(13, "W001", "Chicken Wrap",            "Wrap",     259),
    _p(14, "W002", "Veg Wrap",                "Wrap",     239),
    _p(15, "D001", "Cola Regular",            "Beverage", 99),
    _p(16, "D002", "Cola Medium",             "Beverage", 119),
    _p(17, "D003", "Lemon Soda Regular",      "Beverage", 99),
    _p(18, "D004", "Orange Soda Medium",      "Beverage", 119,  "None", "All"),
    _p(19, "D005", "Cola Large",              "Beverage", 139),
]
