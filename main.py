import pandas as pd
import os
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.panel import Panel
from rich.text import Text

# Initialize Rich console
console = Console()

# Directory containing the CSV files
data_dir = './data'

# Specific stocks to process (without .csv)
target_files = ['AAPL', 'WMT', 'GOOGL', 'AMZN', 'MSFT', 'TSLA', 'META', 'NFLX', 'BA', 'DIS', 'PYPL', 'V', 'MA', 'INTC', 'IBM', 'AMD']
# target_files = [f.split('.')[0] for f in os.listdir(data_dir) if f.endswith('.csv')]

# Date for purchasing the stock
purchase_date = '2024-03-01'

# Total budget and split percentage
total_budget = 900
split_percentage = 1 / len(target_files)  # Equal split for each stock

# Initialize results dictionary
results = {}

# Ensure the directory exists and has files
if not os.path.exists(data_dir) or not os.listdir(data_dir):
    console.print("[bold red]No files found in the data directory.[/bold red]")
    exit()

# Initialize progress bar
with Progress() as progress:
    task = progress.add_task("[cyan]Processing stock files...", total=len(target_files))
    
    # Process files
    for stock_name in target_files:
        file_name = f"{stock_name}.csv"
        file_path = os.path.join(data_dir, file_name)
        
        if not os.path.exists(file_path):
            console.print(f"[yellow]File {file_name} not found. Skipping.[/yellow]")
            progress.advance(task)
            continue
        
        try:
            # Read the CSV file
            data = pd.read_csv(file_path)
            
            # Check for required columns
            if not {'Date', 'Low', 'Close'}.issubset(data.columns):
                console.print(f"[yellow]Required columns not found in {file_name}. Skipping.[/yellow]")
                progress.advance(task)
                continue
            
            # Convert 'Date' column to datetime with explicit UTC handling
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce', utc=True)
            
            # Drop rows where 'Date' conversion failed
            data = data.dropna(subset=['Date'])
            
            # Filter for the purchase date
            purchase_row = data[data['Date'].dt.strftime('%Y-%m-%d') == purchase_date]
            if purchase_row.empty:
                console.print(f"[yellow]Purchase date not found in {file_name}. Skipping.[/yellow]")
                progress.advance(task)
                continue
            
            # Get the lowest price on the purchase date
            purchase_price = purchase_row['Low'].values[0]
            
            # Get the last available row (latest price)
            last_row = data.iloc[-1]
            selling_price = last_row['Close']
            
            # Calculate number of shares bought with the allocated budget
            budget_for_stock = total_budget * split_percentage
            shares_bought = budget_for_stock / purchase_price
            
            # Calculate profit or loss
            profit = shares_bought * selling_price - budget_for_stock
            
            # Calculate profit percentage
            profit_percentage = (profit / budget_for_stock) * 100
            
            # Store the result
            results[stock_name] = {
                'Shares Bought': shares_bought,
                'Purchase Price': purchase_price,
                'Selling Price': selling_price,
                'Profit': profit,
                'Profit Percentage': profit_percentage
            }
        
        except Exception as e:
            console.print(f"[red]Error processing {file_name}: {e}[/red]")
        
        finally:
            progress.advance(task)

# Calculate combined profit
total_profit = sum(result['Profit'] for result in results.values())
total_profit_percent = (total_profit / total_budget) * 100

# Sort the results by profit (from highest to lowest)
sorted_results = sorted(results.items(), key=lambda x: x[1]['Profit'], reverse=True)

# Create a Rich table for results
table = Table(title="Stock Investment Results", title_style="bold magenta")

table.add_column("Stock", style="cyan", no_wrap=True)
table.add_column("Shares Bought", style="green", justify="right")
table.add_column("Purchase Price", style="green", justify="right")
table.add_column("Selling Price", style="green", justify="right")
table.add_column("Profit", style="green", justify="right")
table.add_column("Profit %", style="green", justify="right")

for stock, result in sorted_results:
    profit_color = "green" if result['Profit'] >= 0 else "red"
    profit_text = f"[{profit_color}]{result['Profit']:.2f}[/{profit_color}]"
    profit_percent_text = f"[{profit_color}]{result['Profit Percentage']:.2f}%[/{profit_color}]"
    
    table.add_row(
        stock,
        f"{result['Shares Bought']:.4f}",
        f"${result['Purchase Price']:.2f}",
        f"${result['Selling Price']:.2f}",
        profit_text,
        profit_percent_text
    )

# Add a total row
table.add_section()
table.add_row(
    "[bold]Total[/bold]",
    "",
    "",
    "",
    f"[bold]{total_profit:.2f}[/bold]",
    f"[bold]{total_profit_percent:.2f}%[/bold]"
)

# Display the table within a panel
console.print(Panel(table, border_style="bold blue"))

# If no results, display a message
if not sorted_results:
    console.print("[bold red]No results to display.[/bold red]")
