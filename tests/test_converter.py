import io
import unittest
from pathlib import Path

from openpyxl import load_workbook

from app import app
from converter import ConversionError, Movement, WelfareLookup, convert


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "Kit Candidato" / "input"
CASES = {
    "A": ("4012", "ProviderA_welfare_report_2026-09-01_2026-09-30.xlsx"),
    "B": ("4027", "ProviderB_Flusso-Payroll-01_10_2026.csv"),
    "C": ("4041", "ProviderC_Erogazioni_fatt_031900.xls"),
    "D": ("4093", "ProviderD_tracciato_set26.csv"),
    "E": ("4131", "ProviderE_welfare_settembre_2026.xlsx"),
}


def sample(provider):
    company, filename = CASES[provider]
    return convert(provider, company, "202609", filename, (INPUT / filename).read_bytes())


class ConverterTests(unittest.TestCase):
    def test_provider_a_excludes_employee_missing_from_anagrafica(self):
        result = sample("A")
        expected = (ROOT / "Kit Candidato" / "esempio_output" / "ESEMPIO_VOCI_4012_202609.txt").read_bytes()
        expected_without_unlisted_or_duplicated_employee = b"".join(
            record for record in expected.splitlines(keepends=True)
            if record[6:12].strip() not in (b"25", b"10")
        )
        self.assertEqual(result.content.encode("ascii"), expected_without_unlisted_or_duplicated_employee)
        self.assertEqual((result.input_rows, result.converted_rows, result.output_rows), (21, 16, 14))
        self.assertEqual(len(result.issues), 5)
        self.assertEqual(result.issues[0].row, 8)
        self.assertIn("dipendente non trovato", result.issues[0].detail)
        noemi_issues = [issue for issue in result.issues if issue.person == "Noemi La Rocca"]
        self.assertEqual([issue.row for issue in noemi_issues], [10, 13, 15, 25])
        self.assertTrue(all(issue.detail == "Dipendente duplicato in due aziende (4012,4175)" for issue in noemi_issues))

    def test_all_providers_use_the_same_fixed_width_output(self):
        for provider in CASES:
            with self.subTest(provider=provider):
                result = sample(provider)
                records = result.content.splitlines()
                self.assertEqual(len(records), result.output_rows)
                self.assertTrue(all(len(record) == 38 and record.isascii() for record in records))
                keys = [(int(record[6:12].strip()), record[12:16].strip()) for record in records]
                self.assertEqual(keys, sorted(keys))
                self.assertEqual(len(keys), len(set(keys)))
                self.assertEqual(result.input_rows, result.converted_rows + len(result.issues))

    def test_provider_specific_decisions(self):
        c_records = sample("C").content.splitlines()
        self.assertIn("00404120    194 0000000000031210202609", c_records)
        d_records = sample("D").content.splitlines()
        self.assertIn("00409338    373 0000000000075181202609", d_records)
        self.assertTrue(any(issue.person == "Laura Ferrari Galli" and issue.detail == "Dipendente duplicato in due aziende (4093,4175)" for issue in sample("D").issues))
        e_records = sample("E").content.splitlines()
        self.assertIn("00413115000 371 0000000000009594202609", e_records)
        self.assertIn("00413115039 370 0000000000036800202609", e_records)
        b = sample("B")
        self.assertTrue(any("X71133" in issue.detail for issue in b.issues))
        self.assertEqual(b.output_rows, 6)

    def test_company_scope_and_tax_spelling(self):
        company, filename = CASES["A"]
        data = (INPUT / filename).read_bytes()
        other_company = convert("A", "4175", "202609", filename, data)
        self.assertEqual(other_company.converted_rows, 0)
        self.assertEqual(other_company.output_rows, 0)
        self.assertEqual(len(other_company.issues), 21)
        self.assertEqual(sum(issue.person == "Noemi La Rocca" for issue in other_company.issues), 4)

        lookup = WelfareLookup()
        for spelling in ("Benefit art.51 c.2 let f-bis", "BENEFIT ART.51 C.2 LETT F.B", "Benefit art.51 c.2 lett f-b"):
            with self.subTest(spelling=spelling):
                movement = Movement(1, "", "", "", "", spelling, "", "10,00")
                self.assertEqual(lookup.find(movement), "373")
        effective = Movement(1, "", "", "", "", "Art. 51 c.3", "Effettivo", "10,00")
        self.assertEqual(lookup.find(effective), "194")

    def test_validation_and_http_upload(self):
        company, filename = CASES["A"]
        data = (INPUT / filename).read_bytes()
        with self.assertRaises(ConversionError):
            convert("A", company, "202613", filename, data)
        with app.test_client() as client:
            response = client.post("/api/convert", data={
                "provider": "A", "company": "4012", "period": "202609",
                "file": (io.BytesIO(data), filename),
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["output_rows"], 14)
            self.assertEqual(len(response.json["issues"]), 5)
            self.assertEqual(response.json["filename"], "VOCI_4012_202609.txt")
            invalid = client.post("/api/convert", data={"provider": "A"})
            self.assertEqual(invalid.status_code, 400)

    def test_period_must_match_dates_in_every_provider(self):
        for provider, (company, filename) in CASES.items():
            with self.subTest(provider=provider):
                with self.assertRaisesRegex(ConversionError, "Data non coerente con il periodo selezionato \\(202607\\).*202609"):
                    convert(provider, company, "202607", filename, (INPUT / filename).read_bytes())

        filename = CASES["A"][1]
        workbook = load_workbook(INPUT / filename)
        workbook.active["I5"] = "2026-07-03"
        edited = io.BytesIO()
        workbook.save(edited)
        with self.assertRaisesRegex(ConversionError, "202607: 1 righe \\(es. 5\\)"):
            convert("A", "4012", "202609", filename, edited.getvalue())

        with app.test_client() as client:
            response = client.post("/api/convert", data={
                "provider": "A", "company": "4012", "period": "202607",
                "file": (io.BytesIO((INPUT / filename).read_bytes()), filename),
            })
            self.assertEqual(response.status_code, 400)
            self.assertIn("Data non coerente", response.json["error"])
            self.assertNotIn("content", response.json)


if __name__ == "__main__":
    unittest.main()
