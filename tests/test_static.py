import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class KisanGatiV2StaticTests(unittest.TestCase):
    def setUp(self):
        self.app_source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.db_source = (ROOT / "database.py").read_text(encoding="utf-8")
        self.schema = (ROOT / "supabase" / "schema.sql").read_text(encoding="utf-8")

    def test_python_parses(self):
        ast.parse(self.app_source)
        ast.parse(self.db_source)

    def test_sqlite_is_not_used_by_deployed_app(self):
        self.assertNotIn("import sqlite3", self.app_source)
        self.assertNotIn("procurement.db", self.app_source)
        self.assertNotIn("/tmp/kisangati_procurement.db", self.app_source)

    def test_supabase_postgres_layer_exists(self):
        self.assertIn("psycopg", self.db_source)
        self.assertIn("DATABASE_URL", self.db_source)
        self.assertIn("prepare_threshold=None", self.db_source)
        self.assertIn("sslmode", self.db_source)

    def test_persistent_state_tables_exist(self):
        for table in (
            "farmers",
            "shipment_tracking",
            "tracking_updates",
            "farmer_effort",
            "lot_trace",
            "rejection_records",
            "app_state",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", self.schema)

    def test_persistent_queue_and_token_helpers(self):
        self.assertIn("allocate_token_number", self.app_source)
        self.assertIn("get_current_queue_token", self.app_source)
        self.assertIn("advance_queue_token", self.app_source)

    def test_health_endpoint_exists(self):
        self.assertIn('@app.route("/api/health")', self.app_source)


if __name__ == "__main__":
    unittest.main()
