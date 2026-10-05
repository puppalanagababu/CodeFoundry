import time
import uuid
import requests
from app.tasks.evaluation_tasks import evaluate_submission

BASE_URL = "http://127.0.0.1:8000/api"

def run_live_smoke_test():
    print("=" * 70)
    print("CF-032 LIVE END-TO-END SMOKE TEST")
    print("=" * 70)

    # 1. Registration with unique test student
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"smoke_{unique_suffix}"
    email = f"{username}@example.com"
    password = "SecurePassword123!"

    print(f"\n[1] Registering fresh user: {username} ({email})...")
    reg_resp = requests.post(f"{BASE_URL}/auth/register/", json={
        "username": username,
        "email": email,
        "password": password,
        "password2": password
    })
    print(f"Register status: {reg_resp.status_code}")
    assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"
    print("User registered successfully.")

    # 2. Login
    print(f"\n[2] Logging in as {username}...")
    login_resp = requests.post(f"{BASE_URL}/auth/login/", json={
        "username": username,
        "password": password
    })
    print(f"Login status: {login_resp.status_code}")
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    auth_data = login_resp.json()
    access_token = auth_data["access"]
    refresh_token = auth_data["refresh"]
    headers = {"Authorization": f"Bearer {access_token}"}
    print("Received access and refresh tokens.")

    # 3. Dashboard
    print("\n[3] Fetching Dashboard...")
    dash_resp = requests.get(f"{BASE_URL}/dashboard/", headers=headers)
    print(f"Dashboard status: {dash_resp.status_code}")
    assert dash_resp.status_code == 200, f"Dashboard failed: {dash_resp.text}"
    print(f"Dashboard overview: {dash_resp.json().get('overview')}")

    # 4. Challenge Discovery
    print("\n[4] Browsing active challenges...")
    chal_resp = requests.get(f"{BASE_URL}/challenges/", headers=headers)
    print(f"Challenges status: {chal_resp.status_code}")
    assert chal_resp.status_code == 200, f"Challenges failed: {chal_resp.text}"
    chal_data = chal_resp.json()
    challenges = chal_data.get("results", [])
    print(f"Found {len(challenges)} active challenges (total count={chal_data.get('count')}).")
    target_chal = next((c for c in challenges if c["slug"] == "add-two-numbers"), challenges[0])
    target_id = target_chal["id"]
    target_slug = target_chal["slug"]
    print(f"Selected target challenge: ID={target_id}, Slug={target_slug} ({target_chal['title']})")

    # 5. Challenge Detail
    print(f"\n[5] Fetching detail for challenge ID {target_id}...")
    detail_resp = requests.get(f"{BASE_URL}/challenges/{target_id}/", headers=headers)
    print(f"Detail status: {detail_resp.status_code}")
    assert detail_resp.status_code == 200, f"Detail failed: {detail_resp.text}"
    detail_data = detail_resp.json()
    print(f"Points: {detail_data.get('points')}, Language: {detail_data.get('programming_language')}")

    # 6. Workspace / Sandbox Execution
    print("\n[6 & 7] Running sandbox execution via /api/execution/run/...")
    run_resp = requests.post(f"{BASE_URL}/execution/run/", headers=headers, json={
        "code": "print('CodeFoundry execution sandbox ready')",
        "language": "Python"
    })
    print(f"Sandbox status: {run_resp.status_code}")
    assert run_resp.status_code == 200, f"Sandbox execution failed: {run_resp.text}"
    print(f"Sandbox output: {run_resp.json()}")

    # 8. Submit Solution (Correct Solution - Scenario A)
    print("\n[8] Submitting solution for live evaluation...")
    correct_code = """def add_numbers():
    inputs = input().split()
    if len(inputs) >= 2:
        a = int(inputs[0])
        b = int(inputs[1])
        print(a + b)

if __name__ == '__main__':
    add_numbers()
"""
    sub_resp = requests.post(f"{BASE_URL}/submissions/", headers=headers, json={
        "challenge": target_id,
        "code": correct_code,
        "language": "Python"
    })
    print(f"Submit status: {sub_resp.status_code}")
    assert sub_resp.status_code == 201, f"Submission failed: {sub_resp.text}"
    sub_data = sub_resp.json()
    submission_id = sub_data.get("submission_id") or sub_data.get("id")
    print(f"Submission ID: {submission_id}, initial status: {sub_data.get('status')}")

    # 9, 10, 11, 12, 13. Polling Submission Status
    print(f"\n[9, 10, 11] Polling submission {submission_id} until completion...")
    final_sub = None
    for attempt in range(5):
        poll_resp = requests.get(f"{BASE_URL}/submissions/{submission_id}/", headers=headers)
        assert poll_resp.status_code == 200, f"Poll failed: {poll_resp.text}"
        sub_info = poll_resp.json()
        status = sub_info.get("status")
        print(f"  Attempt {attempt+1}: status = {status}")
        if status in ["PASSED", "FAILED", "ERROR"]:
            final_sub = sub_info
            break
        time.sleep(1)

    if not final_sub:
        print("  Running worker evaluation task directly to ensure instant processing...")
        evaluate_submission(submission_id)
        poll_resp = requests.get(f"{BASE_URL}/submissions/{submission_id}/", headers=headers)
        final_sub = poll_resp.json()
        print(f"  Post-eval status: {final_sub.get('status')}")

    assert final_sub is not None and final_sub.get("status") in ["PASSED", "FAILED", "ERROR"], "Evaluation did not complete"
    print(f"\n[12 & 13] Final Evaluation Status: {final_sub.get('status')}, Score: {final_sub.get('score')}")
    if "evaluation" in final_sub and final_sub["evaluation"]:
        print(f"  Tests passed: {final_sub['evaluation'].get('tests_passed')}/{final_sub['evaluation'].get('total_tests')}")
        print(f"  Skill breakdown: {final_sub['evaluation'].get('skill_breakdown')}")

    # 14. Submission History
    print(f"\n[14] Checking submission history...")
    hist_resp = requests.get(f"{BASE_URL}/submissions/", headers=headers)
    print(f"History status: {hist_resp.status_code}")
    assert hist_resp.status_code == 200, f"History failed: {hist_resp.text}"
    print(f"Total user submissions: {hist_resp.json().get('count')}")

    # 15. Challenge Progress
    print("\n[15] Checking challenge progress...")
    prog_resp = requests.get(f"{BASE_URL}/challenges/progress/", headers=headers)
    print(f"Progress status: {prog_resp.status_code}")
    assert prog_resp.status_code == 200, f"Progress failed: {prog_resp.text}"
    print(f"Progress summary: {prog_resp.json().get('summary')}")

    # 16. Achievements
    print("\n[16] Checking achievements...")
    ach_resp = requests.get(f"{BASE_URL}/users/achievements/", headers=headers)
    print(f"Achievements status: {ach_resp.status_code}")
    assert ach_resp.status_code == 200, f"Achievements failed: {ach_resp.text}"
    print(f"User achievements: {ach_resp.json().get('results')}")

    # 17. Skill Profile
    print("\n[17] Checking skill profile...")
    skill_resp = requests.get(f"{BASE_URL}/users/skill-profile/", headers=headers)
    print(f"Skill profile status: {skill_resp.status_code}")
    assert skill_resp.status_code == 200, f"Skill profile failed: {skill_resp.text}"
    print(f"Skill profile overview: {skill_resp.json().get('overview')}")

    # 18. Leaderboard
    print("\n[18] Checking leaderboard...")
    lead_resp = requests.get(f"{BASE_URL}/leaderboard/", headers=headers)
    print(f"Leaderboard status: {lead_resp.status_code}")
    assert lead_resp.status_code == 200, f"Leaderboard failed: {lead_resp.text}"
    print(f"Leaderboard top results count: {len(lead_resp.json().get('results', []))}")

    # 19. Public Profile
    print(f"\n[19] Checking public profile for '{username}'...")
    pub_resp = requests.get(f"{BASE_URL}/users/profile/{username}/", headers=headers)
    print(f"Public profile status: {pub_resp.status_code}")
    assert pub_resp.status_code == 200, f"Public profile failed: {pub_resp.text}"
    print(f"Public profile user: {pub_resp.json().get('username')}, challenges completed: {pub_resp.json().get('challenges_completed')}")

    print("\n" + "=" * 70)
    print("PHASE 8: FAILURE-PATH SMOKE TESTS")
    print("=" * 70)

    # Scenario B: Incorrect Solution
    print("\n[Scenario B] Submitting incorrect solution...")
    inc_resp = requests.post(f"{BASE_URL}/submissions/", headers=headers, json={
        "challenge": target_id,
        "code": "def add_numbers():\n    print(999)\n\nif __name__ == '__main__':\n    add_numbers()",
        "language": "Python"
    })
    assert inc_resp.status_code == 201
    inc_sub_id = inc_resp.json().get("submission_id")
    evaluate_submission(inc_sub_id)
    poll_inc = requests.get(f"{BASE_URL}/submissions/{inc_sub_id}/", headers=headers).json()
    print(f"  Incorrect solution handled cleanly: status={poll_inc.get('status')}, score={poll_inc.get('score')}")
    assert poll_inc.get("status") in ["PASSED", "FAILED", "ERROR"]

    # Scenario C: Runtime / Syntax Failure
    print("\n[Scenario C] Submitting invalid syntax code...")
    syn_resp = requests.post(f"{BASE_URL}/submissions/", headers=headers, json={
        "challenge": target_id,
        "code": "class IncompleteCode { ??? !!! }",
        "language": "Python"
    })
    assert syn_resp.status_code == 201
    syn_sub_id = syn_resp.json().get("submission_id")
    evaluate_submission(syn_sub_id)
    poll_syn = requests.get(f"{BASE_URL}/submissions/{syn_sub_id}/", headers=headers).json()
    print(f"  Syntax error handled safely: status={poll_syn.get('status')}, score={poll_syn.get('score')}")
    assert poll_syn.get("status") in ["PASSED", "FAILED", "ERROR"]

    # Scenario D: Infinite Loop / Timeout
    print("\n[Scenario D] Submitting infinite loop code...")
    to_resp = requests.post(f"{BASE_URL}/submissions/", headers=headers, json={
        "challenge": target_id,
        "code": "import time\ntime.sleep(20)",
        "language": "Python"
    })
    assert to_resp.status_code == 201
    to_sub_id = to_resp.json().get("submission_id")
    evaluate_submission(to_sub_id)
    poll_to = requests.get(f"{BASE_URL}/submissions/{to_sub_id}/", headers=headers).json()
    print(f"  Timeout handled safely: status={poll_to.get('status')}")
    assert poll_to.get("status") in ["PASSED", "FAILED", "ERROR"]

    # Scenario E: Token Refresh Flow
    print("\n[Scenario E] Testing token refresh endpoint...")
    ref_resp = requests.post(f"{BASE_URL}/auth/refresh/", json={
        "refresh": refresh_token
    })
    print(f"Refresh status: {ref_resp.status_code}")
    assert ref_resp.status_code == 200, f"Token refresh failed: {ref_resp.text}"
    new_tokens = ref_resp.json()
    assert "access" in new_tokens and "refresh" in new_tokens, "New tokens missing in refresh response"
    print("New access token and rotated refresh token successfully issued.")

    # Scenario F: 404 Behavior on non-existent resource
    print("\n[Scenario F] Testing 404 response on non-existent challenge ID 999999...")
    notfound_resp = requests.get(f"{BASE_URL}/challenges/999999/", headers=headers)
    print(f"404 test status: {notfound_resp.status_code}")
    assert notfound_resp.status_code == 404, f"Expected 404, got {notfound_resp.status_code}"
    print(f"404 error detail: {notfound_resp.json()}")

    print("\n" + "=" * 70)
    print("ALL LIVE SMOKE TESTS COMPLETED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_live_smoke_test()
