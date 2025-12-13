import re
import pandas as pd


def make_synthetic_data() -> pd.DataFrame:
    """Crea un DataFrame sintético con algunos errores a propósito."""
    return pd.DataFrame(
        {
            "user_id": [1, 2, 2, 4, 5],
            "email": ["rod@example.com", "bademail", "ana@test.com", None, "sofia@mail.com"],
            "age": [37, 200, 25, 30, -5],
            "status": ["active", "active", "unknown", "inactive", "active"],
        }
    )


def run_quality_checks(df: pd.DataFrame, rules: list[dict]) -> dict:
    """
    Mini DSL: cada regla es un dict con:
      - type: "not_null" | "unique" | "in_range" | "regex" | "in_set"
      - column: nombre de columna
      - params extra según el type
    """
    results = []
    for rule in rules:
        rtype = rule["type"]
        col = rule["column"]

        if col not in df.columns:
            results.append(
                {"rule": rule, "passed": False, "failed_rows": len(df), "failed_idx": df.index.tolist(),
                 "message": f"Column '{col}' no existe"}
            )
            continue

        s = df[col]

        if rtype == "not_null":
            fail = s.isna()

        elif rtype == "unique":
            # ignora NaN al evaluar duplicados
            non_null = s.dropna()
            dup_vals = non_null[non_null.duplicated(keep=False)]
            fail = s.isin(dup_vals)

        elif rtype == "in_range":
            min_v = rule.get("min")
            max_v = rule.get("max")
            num = pd.to_numeric(s, errors="coerce")  # no numérico => NaN
            fail = num.isna()
            if min_v is not None:
                fail |= num < min_v
            if max_v is not None:
                fail |= num > max_v

        elif rtype == "regex":
            pattern = rule["pattern"]
            rx = re.compile(pattern)
            # None => "" para que falle
            fail = ~s.fillna("").astype(str).apply(lambda x: bool(rx.match(x)))

        elif rtype == "in_set":
            allowed = set(rule["allowed"])
            fail = ~s.isin(allowed)

        else:
            results.append(
                {"rule": rule, "passed": False, "failed_rows": len(df), "failed_idx": df.index.tolist(),
                 "message": f"Rule type '{rtype}' no soportada"}
            )
            continue

        failed_idx = df.index[fail].tolist()
        results.append(
            {
                "rule": rule,
                "passed": len(failed_idx) == 0,
                "failed_rows": len(failed_idx),
                "failed_idx": failed_idx,
                "message": "OK" if len(failed_idx) == 0 else f"Fallan {len(failed_idx)} fila(s)",
            }
        )

    summary = {
        "total_rules": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
    }
    return {"summary": summary, "results": results}


def print_report(report: dict) -> None:
    print("\n=== DATA QUALITY REPORT ===")
    print(report["summary"])
    for r in report["results"]:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"{status} | {r['rule']} | {r['message']} | idx={r['failed_idx']}")


def main():
    df = make_synthetic_data()
    print("=== DATASET ===")
    print(df)

    # Mini DSL (reglas)
    rules = [
        {"type": "not_null", "column": "email"},
        {"type": "regex", "column": "email", "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
        {"type": "in_range", "column": "age", "min": 0, "max": 120},
        {"type": "in_set", "column": "status", "allowed": ["active", "inactive"]},
        {"type": "unique", "column": "user_id"},
    ]

    report = run_quality_checks(df, rules)
    print_report(report)

    # BONUS: muestra filas problemáticas (uniendo todos los índices fallidos)
    bad_idx = sorted({i for r in report["results"] for i in r["failed_idx"]})
    if bad_idx:
        print("\n=== Filas con al menos 1 falla ===")
        print(df.loc[bad_idx])


if __name__ == "__main__":
    main()
