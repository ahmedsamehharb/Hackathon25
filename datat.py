import pandas as pd

issues = pd.read_csv('Data/complete_issues_data.csv')
daily = pd.read_csv('Data/daily_aggregated.csv')
monthly = pd.read_csv('Data/monthly_aggregated.csv')
weekly = pd.read_csv('Data/weekly_aggregated.csv')

# header
print("Issues:\n", issues.head())
print("Daily Aggregated:\n", daily.head())
print("Monthly Aggregated:\n", monthly.head())
print("Weekly Aggregated:\n", weekly.head())

issues['timestamp'] = pd.to_datetime(issues['timestamp'])
issues['date'] = pd.to_datetime(issues['date'])  # Already exists in file
#monthly['month'] = pd.to_datetime(monthly['month'], format='%Y-%m')
weekly['week'] = pd.to_datetime(weekly['week'].str[:10])  # Get week start

# Add year, month, etc.
issues['year'] = issues['timestamp'].dt.year
issues['month_num'] = issues['timestamp'].dt.month
issues['day_of_week'] = issues['timestamp'].dt.day_name()

# Sort each dataframe chronologically
issues = issues.sort_values('timestamp')
daily = daily.sort_values('date')
weekly = weekly.sort_values('week')
monthly = monthly.sort_values('month')


available_categories = sorted(issues['category'].dropna().unique())
available_genders = sorted(issues['gender'].dropna().unique())
available_states = sorted(issues['state'].dropna().unique())
available_age_groups = sorted(issues['age_group'].dropna().unique())

#issues_by_state = issues.groupby('state').size().reset_index(name='issue_count')
#issues_by_category = issues.groupby('category').size().reset_index(name='issue_count')
#issues_by_gender = issues.groupby('gender').size().reset_index(name='issue_count')