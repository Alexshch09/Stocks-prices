import pandas as pd
import os

# Directory containing the CSV files
data_dir = './data'

# Specific stocks to process (without .csv)
target_files = ['AAPL', 'WMT', 'GOOGL', 'AMZN', 'MSFT', 'TSLA', 'META', 'NFLX', 'BA', 'DIS', 'PYPL', 'V', 'MA', 'INTC', 'IBM', 'AMD']

# Monthly investment details
monthly_budget = 100
split_percentage = 1 / len(target_files)  # Split equally across stocks

# Date from which to start investing
start_investment_date = pd.to_datetime('2024-03-01').tz_localize('UTC')

# Initialize results dictionary
results = {}
investment_history = {stock: [] for stock in target_files}

# Ensure the directory exists and has files
if not os.path.exists(data_dir) or not os.listdir(data_dir):
    print("No files found in the data directory.")
    exit()

for stock_name in target_files:
    file_name = f"{stock_name}.csv"
    file_path = os.path.join(data_dir, file_name)
    
    if not os.path.exists(file_path):
        print(f"File {file_name} not found. Skipping.")
        continue
    
    try:
        # Read the CSV file
        data = pd.read_csv(file_path)
        
        # Check for required columns
        if not {'Date', 'Low', 'Close'}.issubset(data.columns):
            print(f"Required columns not found in {file_name}. Skipping.")
            continue
        
        # Convert 'Date' column to datetime with UTC handling
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce', utc=True)
        data = data.dropna(subset=['Date']).sort_values(by='Date')
        
        # Filter data starting from March 1st, 2024
        data = data[data['Date'] >= start_investment_date]
        
        if data.empty:
            print(f"No data available after {start_investment_date} for {file_name}. Skipping.")
            continue
        
        # Extract date range for investments
        start_date = data['Date'].iloc[0]
        end_date = data['Date'].iloc[-1]
        
        # Generate a range of investment dates (monthly)
        monthly_dates = pd.date_range(start=start_date, end=end_date, freq='MS')
        
        # Track shares purchased
        total_shares = 0
        total_investment = 0
        
        for invest_date in monthly_dates:
            # Find the closest date in the dataset for this investment
            available_row = data[data['Date'] <= invest_date].iloc[-1:]
            if available_row.empty:
                continue
            
            # Use the "Low" price for purchasing shares
            low_price = available_row['Low'].values[0]
            monthly_allocation = monthly_budget * split_percentage
            shares_bought = monthly_allocation / low_price
            
            # Update investment totals
            total_shares += shares_bought
            total_investment += monthly_allocation
            investment_history[stock_name].append({
                'Date': invest_date,
                'Shares Bought': shares_bought,
                'Price': low_price
            })
        
        # Final price for profit calculation
        final_close_price = data['Close'].iloc[-1]
        profit = total_shares * final_close_price - total_investment
        profit_percentage = (profit / total_investment) * 100 if total_investment > 0 else 0
        
        # Store the result
        results[stock_name] = {
            'Total Shares': total_shares,
            'Total Investment': total_investment,
            'Final Price': final_close_price,
            'Profit': profit,
            'Profit Percentage': profit_percentage
        }
    
    except Exception as e:
        print(f"Error processing {file_name}: {e}")

# Calculate combined profit
total_profit = sum(result['Profit'] for result in results.values())
total_investment = sum(result['Total Investment'] for result in results.values())

# Handle potential division by zero when calculating profit percentage
total_profit_percent = (total_profit / total_investment) * 100 if total_investment > 0 else 0

# Sort the results by profit (from highest to lowest)
sorted_results = sorted(results.items(), key=lambda x: x[1]['Profit'], reverse=True)

# Print results
if sorted_results:
    print(f"{'Stock':<10} {'Total Shares':<15} {'Total Investment':<20} {'Final Price':<15} {'Profit':<10} {'Profit %':<10}")
    print("=" * 90)
    
    for stock, result in sorted_results:
        print(f"{stock:<10} {result['Total Shares']:<15.4f} {result['Total Investment']:<20.2f} {result['Final Price']:<15.2f} {result['Profit']:<10.2f} {result['Profit Percentage']:<10.2f}")
    
    print("=" * 90)
    print(f"{'Total':<10} {'':<15} {total_investment:<20.2f} {'':<15} {total_profit:<10.2f} {total_profit_percent:.2f}%")
else:
    print("No results to display.")
