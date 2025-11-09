import polars as pl
import numpy as np
from datetime import datetime, timedelta

# Set up for consistent results
np.random.seed(42)

# Create realistic coffee shop data
def generate_coffee_data():
    n_records = 2000
    # Coffee menu items with realistic prices
    menu_items = ['Espresso', 'Cappuccino', 'Latte', 'Americano', 'Mocha', 'Cold Brew']
    prices = [2.50, 4.00, 4.50, 3.00, 5.00, 3.50]
    price_map = dict(zip(menu_items, prices))

    # Generate dates over 6 months
    start_date = datetime(2023, 6, 1)
    dates = [start_date + timedelta(days=np.random.randint(0, 180))
             for _ in range(n_records)]

    # Randomly select drinks, then map the correct price for each selected drink
    drinks = np.random.choice(menu_items, n_records)
    prices_chosen = [price_map[d] for d in drinks]

    data = {
        'date': dates,
        'drink': drinks,
        'price': prices_chosen,
        'quantity': np.random.choice([1, 1, 1, 2, 2, 3], n_records),
        'customer_type': np.random.choice(['Regular', 'New', 'Tourist'],
                                          n_records, p=[0.5, 0.3, 0.2]),
        'payment_method': np.random.choice(['Card', 'Cash', 'Mobile'],
                                           n_records, p=[0.6, 0.2, 0.2]),
        'rating': np.random.choice([2, 3, 4, 5], n_records, p=[0.1, 0.4, 0.4, 0.1])
    }
    return data

# Create our coffee shop DataFrame
coffee_data = generate_coffee_data()
df = pl.DataFrame(coffee_data)

# Take a peek at your data
print("First 5 transactions:")
print(df.head())

print("\nWhat types of data do we have?")
print(df.schema)

print("\nHow big is our dataset?")
print(f"We have {df.height} transactions and {df.width} columns")

# Calculate total sales amount and add useful date information
df_enhanced = df.with_columns([
    # Calculate revenue per transaction
    (pl.col('price') * pl.col('quantity')).alias('total_sale'),

    # Extract useful date components
    pl.col('date').dt.weekday().alias('day_of_week'),
    pl.col('date').dt.month().alias('month'),
    pl.col('date').dt.hour().alias('hour_of_day')
])

print("Sample of enhanced data:")
print(df_enhanced.head())

drink_performance = (df_enhanced
    .group_by('drink')
    .agg([
        pl.col('total_sale').sum().alias('total_revenue'),
        pl.col('quantity').sum().alias('total_sold'),
        pl.col('rating').mean().alias('avg_rating')
    ])
    .sort('total_revenue', descending=True)
)

print("Drink performance ranking:")
print(drink_performance)

# What do the daily sales look like?
daily_patterns = (df_enhanced
    .group_by('day_of_week')
    .agg([
        pl.col('total_sale').sum().alias('daily_revenue'),
        pl.len().alias('number_of_transactions')
    ])
    .sort('day_of_week')
)

print("Daily business patterns:")
print(daily_patterns)

# Find transactions over $10 (multiple items or expensive drinks)
big_orders = (df_enhanced
    .filter(pl.col('total_sale') > 10.0)
    .sort('total_sale', descending=True)
)

print(f"We have {big_orders.height} orders over $10")
print("Top 5 biggest orders:")
print(big_orders.head())

# Analyze customer behavior by type
customer_analysis = (df_enhanced
    .group_by('customer_type')
    .agg([
        pl.col('total_sale').mean().alias('avg_spending'),
        pl.col('total_sale').sum().alias('total_revenue'),
        pl.len().alias('visit_count'),
        pl.col('rating').mean().alias('avg_satisfaction')
    ])
    .with_columns([
        # Calculate revenue per visit
        (pl.col('total_revenue') / pl.col('visit_count')).alias('revenue_per_visit')
    ])
)

print("Customer behavior analysis:")
print(customer_analysis)

# Create a complete business summary
business_summary = {
    'total_revenue': df_enhanced['total_sale'].sum(),
    'total_transactions': df_enhanced.height,
    'average_transaction': df_enhanced['total_sale'].mean(),
    'best_selling_drink': drink_performance.row(0)[0],  # First row, first column
    'customer_satisfaction': df_enhanced['rating'].mean()
}

print("\n=== BEAN THERE COFFEE SHOP - SUMMARY ===")
for key, value in business_summary.items():
    if isinstance(value, float) and key != 'customer_satisfaction':
        print(f"{key.replace('_', ' ').title()}: ${value:.2f}")
    else:
        print(f"{key.replace('_', ' ').title()}: {value}")