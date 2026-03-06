from database import save_report

save_report(
    circular_name="Test Circular",
    parsed_result='{"title": "Test", "severity": "Low"}',
    action_plan="No action needed for test."
)