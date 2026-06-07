import subprocess

tests = [
    ("Account Lookup", "evaluation.test_lookup"),
    ("Verification", "evaluation.test_verification"),
    ("Context Management", "evaluation.test_context"),
    ("Payment Processing", "evaluation.test_payment"),
]

results = []

print("\n" + "=" * 70)
print("PAYMENT COLLECTION AGENT - EVALUATION REPORT")
print("=" * 70)

for test_name, module in tests:

    result = subprocess.run(
        ["uv","run","python", "-m", module],
        capture_output=True,
        text=True
    )

    passed = result.returncode == 0

    results.append((test_name, passed))

    status = "[PASS]" if passed else "[FAIL]"

    print(f"{status:<8} {test_name}")

    if not passed:
        error_lines = result.stderr.strip().split("\n")
        print(f"         Reason: {error_lines[-1]}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

total = len(results)
passed = sum(status for _, status in results)
failed = total - passed

print(f"Total Test Suites : {total}")
print(f"Passed            : {passed}")
print(f"Failed            : {failed}")
print(f"Success Rate      : {(passed / total) * 100:.1f}%")

print("=" * 70)

if failed == 0:
    print("\nAll evaluation suites passed successfully.")
else:
    print("\nSome evaluation suites failed. Review the details above.")