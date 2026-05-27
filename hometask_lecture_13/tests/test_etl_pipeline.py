import nbformat
import pandas as pd


def load_notebook_namespace():
    notebook = nbformat.read("etl_pipeline.ipynb", as_version=4)
    namespace = {}
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        if "test-source" not in cell.metadata.get("tags", []):
            continue
        exec(cell.source, namespace)
    return namespace


ns = load_notebook_namespace()
is_valid_email = ns["is_valid_email"]
clean_customers = ns["clean_customers"]
clean_products = ns["clean_products"]
clean_orders = ns["clean_orders"]
clean_order_items = ns["clean_order_items"]
transform_data = ns["transform_data"]
build_report_frames = ns["build_report_frames"]


def test_valid_email_returns_true_for_normal_email():
    assert is_valid_email("user@example.com") is True


def test_invalid_email_returns_false_for_bad_email_and_missing_value():
    assert is_valid_email("bad-email") is False
    assert is_valid_email(None) is False


def test_clean_customers_removes_missing_id_and_duplicate_id():
    raw = pd.DataFrame(
        {
            "customer_id": [1, 1, None, 2],
            "email": ["a@example.com", "dup@example.com", "x@example.com", "b@example.com"],
            "country": ["US", "US", "UA", "PL"],
            "created_at": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        }
    )

    cleaned = clean_customers(raw)

    assert cleaned["customer_id"].tolist() == [1, 2]


def test_clean_customers_sets_invalid_email_to_null():
    raw = pd.DataFrame(
        {
            "customer_id": [1],
            "email": ["not-an-email"],
            "country": ["US"],
            "created_at": ["2026-01-01"],
        }
    )

    cleaned = clean_customers(raw)

    assert cleaned.loc[0, "email"] is None


def test_clean_customers_removes_invalid_timestamp():
    raw = pd.DataFrame(
        {
            "customer_id": [1, 2],
            "email": ["a@example.com", "b@example.com"],
            "country": ["US", "PL"],
            "created_at": ["2026-01-01", "not-a-date"],
        }
    )

    cleaned = clean_customers(raw)

    assert cleaned["customer_id"].tolist() == [1]


def test_clean_products_removes_duplicate_and_non_positive_prices():
    raw = pd.DataFrame(
        {
            "product_id": [10, 10, 11, 12],
            "name": ["A", "A duplicate", "B", "C"],
            "category": ["Tools", "Tools", "Tools", "Tools"],
            "price": [5.0, 6.0, 0.0, -1.0],
        }
    )

    cleaned = clean_products(raw)

    assert cleaned["product_id"].tolist() == [10]
    assert cleaned.loc[0, "price"] == 5.0


def test_clean_orders_normalizes_status_and_removes_orphans():
    raw = pd.DataFrame(
        {
            "order_id": [100, 101, 102],
            "customer_id": [1, 1, 999],
            "order_status": ["COMPLETED", "strange", "pending"],
            "created_at": ["2026-01-01", "2026-01-02", "2026-01-03"],
        }
    )

    cleaned = clean_orders(raw, valid_customer_ids={1})

    assert cleaned["order_id"].tolist() == [100, 101]
    assert cleaned["order_status"].tolist() == ["completed", "unknown"]


def test_clean_order_items_fixes_negative_quantity_and_removes_orphans():
    raw = pd.DataFrame(
        {
            "order_item_id": [1, 2, 3, 4],
            "order_id": [100, 100, 999, 100],
            "product_id": [10, 10, 10, 999],
            "quantity": [-2, 0, 1, 1],
        }
    )

    cleaned = clean_order_items(raw, valid_order_ids={100}, valid_product_ids={10})

    assert cleaned["order_item_id"].tolist() == [1]
    assert cleaned.loc[0, "quantity"] == 2


def test_transform_data_returns_all_clean_table_names():
    tables = {
        "customers": pd.DataFrame(
            {
                "customer_id": [1],
                "email": ["a@example.com"],
                "country": ["US"],
                "created_at": ["2026-01-01"],
            }
        ),
        "products": pd.DataFrame(
            {
                "product_id": [10],
                "name": ["Widget"],
                "category": ["Tools"],
                "price": [5.0],
            }
        ),
        "orders": pd.DataFrame(
            {
                "order_id": [100],
                "customer_id": [1],
                "order_status": ["completed"],
                "created_at": ["2026-01-02"],
            }
        ),
        "order_items": pd.DataFrame(
            {
                "order_item_id": [1],
                "order_id": [100],
                "product_id": [10],
                "quantity": [2],
            }
        ),
    }

    cleaned = transform_data(tables)

    assert set(cleaned) == {"customers", "products", "orders", "order_items"}
    assert len(cleaned["order_items"]) == 1


def test_build_report_frames_creates_expected_revenue_reports():
    clean_tables = {
        "customers": pd.DataFrame(
            {
                "customer_id": [1],
                "email": ["a@example.com"],
                "country": ["US"],
                "created_at": pd.to_datetime(["2026-01-01"]),
            }
        ),
        "products": pd.DataFrame(
            {
                "product_id": [10],
                "name": ["Widget"],
                "category": ["Tools"],
                "price": [5.0],
            }
        ),
        "orders": pd.DataFrame(
            {
                "order_id": [100, 101],
                "customer_id": [1, 1],
                "order_status": ["completed", "cancelled"],
                "created_at": pd.to_datetime(["2026-01-02", "2026-01-03"]),
            }
        ),
        "order_items": pd.DataFrame(
            {
                "order_item_id": [1, 2],
                "order_id": [100, 101],
                "product_id": [10, 10],
                "quantity": [2, 10],
            }
        ),
    }

    reports = build_report_frames(clean_tables)

    assert set(reports) == {
        "report_customer_summary",
        "report_product_revenue",
        "report_orders_by_status",
        "report_monthly_revenue",
    }
    assert reports["report_customer_summary"].loc[0, "total_orders"] == 1
    assert reports["report_customer_summary"].loc[0, "total_spent"] == 10.0
    assert reports["report_product_revenue"].loc[0, "units_sold"] == 2
    assert reports["report_monthly_revenue"].loc[0, "revenue"] == 10.0
