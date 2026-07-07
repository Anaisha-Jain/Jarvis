from dispatcher import handle_action

print("Initiating silent status report...\n")

# We package the command into a single dictionary so it counts as 1 argument
action_dict = {
    "name": "status_report",
    "params": {}
}

# Now we pass the single dictionary
response = handle_action(action_dict)

print("\n=== J.A.R.V.I.S. MORNING BRIEFING ===")
print(response)
print("=====================================\n")