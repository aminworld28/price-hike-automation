"""A tiny fake admin portal that behaves like a typical vendor-built product admin:
search by code -> Edit page -> Update. The form refuses to save if Type or Service
is unselected, which is the exact trap the automation has to handle.

Run:  python mock_portal/app.py   ->  http://127.0.0.1:5000/products
"""
from flask import Flask, request, redirect, render_template_string
from seed import PRODUCTS

app = Flask(__name__)
DB = {p["id"]: dict(p) for p in PRODUCTS}

CSS = """<style>
body{font-family:system-ui,sans-serif;margin:32px;color:#222}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:8px;border-bottom:1px solid #ddd}
input[type=text],input[type=number]{padding:6px;width:320px}.row{margin:14px 0}.row>span{display:inline-block;width:120px}
label{margin-right:18px}button{padding:8px 22px;background:#222;color:#fff;border:0;cursor:pointer}
.err{background:#fee;border:1px solid #c33;padding:10px;margin-bottom:16px}
</style>"""

LIST_HTML = CSS + """
<h2>Demo Bites Admin - Products</h2>
<form method="get"><input type="text" name="keyword" value="{{ kw }}" placeholder="search code or name">
<button>Search</button></form><br>
<table><thead><tr><th>SN</th><th>NAME</th><th>CODE</th><th>SERVICE</th><th>CATEGORY</th><th>PRICE</th><th>ACTION</th></tr></thead>
<tbody>{% for p in rows %}<tr><td>{{ loop.index }}</td><td>{{ p.name }}</td><td>{{ p.code }}</td>
<td>{{ p.service or 'N/A' }}</td><td>{{ p.category }}</td><td>{{ '%.2f' % p.price }}</td>
<td><a href="/products/{{ p.id }}/edit">Edit</a></td></tr>{% endfor %}</tbody></table>
<p>Showing {{ rows|length }} entries</p>"""

EDIT_HTML = CSS + """
<h2>Edit Product</h2>
{% if error %}<div class="err">{{ error }}</div>{% endif %}
<form method="post">
<div class="row"><span>Category</span><input type="text" value="{{ p.category }}" readonly></div>
<div class="row"><span>Name</span><input type="text" value="{{ p.name }}" readonly></div>
<div class="row"><span>Code</span><input type="text" value="{{ p.code }}" readonly></div>
<div class="row"><span>Price</span><input type="number" name="price" value="{{ p.price }}" required></div>
<div class="row"><span>Status</span>
 <label><input type="radio" name="status" value="Active" {{ 'checked' if p.status=='Active' }}> Active</label>
 <label><input type="radio" name="status" value="Inactive" {{ 'checked' if p.status=='Inactive' }}> Inactive</label></div>
<div class="row"><span>Type</span>
 <label><input type="radio" name="type" value="Veg" required {{ 'checked' if p.type=='Veg' }}> Veg</label>
 <label><input type="radio" name="type" value="Non Veg" {{ 'checked' if p.type=='Non Veg' }}> Non Veg</label>
 <label><input type="radio" name="type" value="None" {{ 'checked' if p.type=='None' }}> None</label></div>
<div class="row"><span>Only For Deal</span>
 <label><input type="radio" name="deal" value="Yes" {{ 'checked' if p.deal=='Yes' }}> Yes</label>
 <label><input type="radio" name="deal" value="No" {{ 'checked' if p.deal=='No' }}> No</label></div>
<div class="row"><span>Service</span>
 <label><input type="radio" name="service" value="All" required {{ 'checked' if p.service=='All' }}> All</label>
 <label><input type="radio" name="service" value="Delivery" {{ 'checked' if p.service=='Delivery' }}> Delivery</label>
 <label><input type="radio" name="service" value="Pickup" {{ 'checked' if p.service=='Pickup' }}> Pickup</label></div>
<button type="submit">Update</button> <a href="/products">Cancel</a>
</form>"""


@app.get("/")
def home():
    return redirect("/products")


@app.get("/products")
def products():
    kw = request.args.get("keyword", "").strip().lower()
    rows = [p for p in DB.values() if not kw or kw in p["code"].lower() or kw in p["name"].lower()]
    return render_template_string(LIST_HTML, rows=rows, kw=kw)


@app.route("/products/<int:pid>/edit", methods=["GET", "POST"])
def edit(pid):
    p = DB.get(pid)
    if not p:
        return "Not found", 404
    if request.method == "POST":
        f = request.form
        if not f.get("type") or not f.get("service"):
            return render_template_string(EDIT_HTML, p=p, error="Type and Service are required."), 400
        p.update(price=int(float(f["price"])), status=f.get("status", p["status"]),
                 type=f["type"], deal=f.get("deal", p["deal"]), service=f["service"])
        return redirect("/products")
    return render_template_string(EDIT_HTML, p=p, error=None)


if __name__ == "__main__":
    app.run(port=5000, debug=False)
