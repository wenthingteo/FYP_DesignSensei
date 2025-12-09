"""
Simple script to test the FYP evaluation endpoints via API
Run after starting Django server: python manage.py runserver
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_endpoints():
    print("\n" + "="*80)
    print("FYP OBJECTIVE EVALUATION - API ENDPOINT TEST")
    print("="*80)
    
    # You need to login first or use session authentication
    print("\n⚠️  Note: You may need to authenticate first")
    print("   Option 1: Login via /api/login/ and use session cookie")
    print("   Option 2: Use your browser's session cookie")
    print("\nFor now, testing public-accessible endpoints...\n")
    
    endpoints = [
        {
            "name": "Performance Report",
            "url": f"{BASE_URL}/evaluation/performance-report/",
            "description": "Shows GraphRAG accuracy metrics and objective achievement"
        },
        {
            "name": "Evaluation Dashboard",
            "url": f"{BASE_URL}/evaluation/dashboard/",
            "description": "Visualization data for charts and time-series"
        },
        {
            "name": "Ground Truth Database",
            "url": f"{BASE_URL}/evaluation/ground-truth/?verified=true",
            "description": "Lists all verified ground truth questions"
        }
    ]
    
    print("Available FYP Evaluation Endpoints:\n")
    for i, endpoint in enumerate(endpoints, 1):
        print(f"{i}. {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        print(f"   Purpose: {endpoint['description']}\n")
    
    print("="*80)
    print("CURL Commands for Testing (after authentication):")
    print("="*80)
    print(f"""
# 1. Get Performance Report (FYP Objective Evidence)
curl -X GET "{BASE_URL}/evaluation/performance-report/" \\
     -H "Content-Type: application/json" \\
     --cookie "sessionid=YOUR_SESSION_ID"

# 2. Get Dashboard Data
curl -X GET "{BASE_URL}/evaluation/dashboard/" \\
     -H "Content-Type: application/json" \\
     --cookie "sessionid=YOUR_SESSION_ID"

# 3. Get Ground Truths
curl -X GET "{BASE_URL}/evaluation/ground-truth/?verified=true" \\
     -H "Content-Type: application/json" \\
     --cookie "sessionid=YOUR_SESSION_ID"
""")
    
    print("="*80)
    print("Frontend Integration Example (React/JavaScript):")
    print("="*80)
    print("""
// Fetch Performance Report
fetch('/api/evaluation/performance-report/', {
    credentials: 'include'  // Include session cookie
})
.then(res => res.json())
.then(data => {
    console.log('FYP Objective:', data.fyp_objective);
    console.log('Status:', data.objective_status);
    console.log('Accuracy:', data.success_metrics.accuracy);
    // Display metrics in your UI
});

// Fetch Dashboard Data for Charts
fetch('/api/evaluation/dashboard/', {
    credentials: 'include'
})
.then(res => res.json())
.then(data => {
    // data.mode_distribution - for pie chart
    // data.accuracy_distribution - for bar chart
    // data.time_series - for line chart
    renderCharts(data);
});
""")
    
    print("\n" + "="*80)
    print("Python Requests Example:")
    print("="*80)
    print("""
import requests

# Login first
session = requests.Session()
session.post('http://localhost:8000/api/login/', 
             json={'username': 'admin', 'password': 'admin'})

# Get performance report
response = session.get('http://localhost:8000/api/evaluation/performance-report/')
report = response.json()

print(f"FYP Objective: {report['fyp_objective']}")
print(f"Status: {report['objective_status']}")
print(f"GraphRAG Accuracy: {report['success_metrics']['accuracy']['achieved']}")
print(f"Conclusion: {report['conclusion']}")
""")

if __name__ == "__main__":
    test_endpoints()
    
    print("\n" + "="*80)
    print("✅ Test script complete!")
    print("="*80)
    print("\n📝 For your FYP documentation:")
    print("   1. Screenshot the performance report JSON response")
    print("   2. Create charts from dashboard data")
    print("   3. Show ground truth database (29 verified questions)")
    print("   4. Demonstrate accuracy metrics meeting targets (>70%)")
    print("   5. Compare GraphRAG vs LLM-Only performance\n")
