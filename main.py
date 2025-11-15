import os
import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuration
CSV_FOLDER = 'csvs'
COLUMNS_TO_IGNORE = ['X_center', 'X_cycle_time', 'X_continuous_level', 'X_cycle_time', 'X_n_steps', 'X_phase', 'X_step_duration', 'X_step_index', 'X_step_progress', 'X_triangle', 'X_within_step']

def get_available_csv_files():
    """Get list of available CSV files"""
    csv_files = []
    if os.path.exists(CSV_FOLDER):
        csv_files = [f for f in os.listdir(CSV_FOLDER) if f.endswith('.csv')]
    return sorted(csv_files)

def create_time_series_plot(csv_path, filename):
    """
    Create the original time series plot
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        if 'time' not in df.columns:
            print(f"Warning: 'time' column not found in {filename}")
            return None
        
        # Identify columns to plot: all except time and ignored columns
        value_vars = [col for col in df.columns 
                     if col != 'time' and col not in COLUMNS_TO_IGNORE]
        
        # Check if we have any columns left to plot
        if not value_vars:
            print(f"No plottable columns found in {filename} after filtering")
            return None
        
        # Melt dataframe to long format for Plotly Express
        df_long = df.melt(id_vars=['time'], value_vars=value_vars, 
                         var_name='variable', value_name='value')
        
        # Create interactive line plot
        fig = px.line(df_long, x='time', y='value', color='variable',
                     title=f"{filename} - Time Series",
                     labels={'value': 'Value', 'time': 'Time'})
        
        # Customize legend and layout
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Value',
            legend_title='Variables',
            hovermode='x unified',
            showlegend=True
        )

        visible_by_default = ['profit_share', 'utilization_rate', 'consumption_rate', 
                             'investment_rate', 'H_stock']

        for trace in fig.data:
            if hasattr(trace, 'name') and trace.name not in visible_by_default:
                trace.visible = 'legendonly'
        
        # Convert to HTML div
        return pio.to_html(fig, full_html=False)
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        return None

def create_parametric_plot(csv_path, filename):
    """
    Create parametric plot with profit_share vs utilization_rate
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Check if required columns exist
        if 'profit_share' not in df.columns or 'utilization_rate' not in df.columns:
            print(f"Warning: Required columns 'profit_share' or 'utilization_rate' not found in {filename}")
            return None
        
        # Create parametric scatter plot
        fig = px.scatter(df, x='profit_share', y='utilization_rate',
                        title=f"{filename} - Parametric Plot",
                        labels={'profit_share': 'Profit Share', 'utilization_rate': 'Utilization Rate'})
        
        # Optional: Add a line to connect the points in order
        fig.add_scatter(x=df['profit_share'], y=df['utilization_rate'], 
                       mode='lines', line=dict(dash='dot', color='gray'),
                       name='trend', showlegend=False)
        
        # Customize layout
        fig.update_layout(
            xaxis_title='Profit Share',
            yaxis_title='Utilization Rate',
            showlegend=False
        )
        
        # Convert to HTML div
        return pio.to_html(fig, full_html=False)
        
    except Exception as e:
        print(f"Error creating parametric plot for {filename}: {str(e)}")
        return None

def create_comparison_plot(selected_files):
    """
    Create a comparison plot with multiple CSV files
    Each curve is colored based on the selection order
    """
    try:
        print(f"Creating comparison plot for files: {selected_files}")
        
        # Define colors for different files
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        fig = go.Figure()
        valid_files_count = 0
        
        for i, filename in enumerate(selected_files):
            csv_path = os.path.join(CSV_FOLDER, filename)
            
            if not os.path.exists(csv_path):
                print(f"File not found: {csv_path}")
                continue
                
            df = pd.read_csv(csv_path)
            print(f"Processing {filename}")
            
            # Check if required columns exist
            if 'profit_share' not in df.columns or 'utilization_rate' not in df.columns:
                print(f"Missing required columns in {filename}")
                continue
            
            color = colors[i % len(colors)]
            
            # Add scatter with lines
            fig.add_trace(go.Scatter(
                x=df['profit_share'],
                y=df['utilization_rate'],
                mode='lines+markers',
                name=filename,
                line=dict(color=color, width=3),
                marker=dict(color=color, size=6)
            ))
            
            valid_files_count += 1
        
        print(f"Successfully added {valid_files_count} traces")
        
        if valid_files_count == 0:
            return None
        
        fig.update_layout(
            title="Parametric Comparison: Profit Share vs Utilization Rate",
            xaxis_title='Profit Share',
            yaxis_title='Utilization Rate',
            height=500
        )
        
        # Convert to JSON for client-side rendering
        return fig.to_json()
        
    except Exception as e:
        print(f"Error creating comparison plot: {str(e)}")
        return None

@app.route('/')
def index():
    """Main dashboard route"""
    time_series_plots = []
    parametric_plots = []
    filenames = []
    
    # Process all CSV files in the csvs folder
    if os.path.exists(CSV_FOLDER):
        for filename in os.listdir(CSV_FOLDER):
            if filename.endswith('.csv'):
                csv_path = os.path.join(CSV_FOLDER, filename)
                
                # Create both types of plots
                time_series_html = create_time_series_plot(csv_path, filename)
                parametric_html = create_parametric_plot(csv_path, filename)
                
                if time_series_html or parametric_html:
                    time_series_plots.append(time_series_html)
                    parametric_plots.append(parametric_html)
                    filenames.append(filename)
    
    csv_files = get_available_csv_files()
    
    return render_template('index.html', 
                         time_series_plots=time_series_plots,
                         parametric_plots=parametric_plots,
                         filenames=filenames,
                         csv_files=csv_files,
                         plot_count=len(filenames))

@app.route('/compare', methods=['POST'])
def compare_files():
    """Endpoint for comparing multiple CSV files"""
    data = request.get_json()
    selected_files = data.get('files', [])
    
    if len(selected_files) < 2:
        return jsonify({'error': 'Please select at least 2 files'}), 400
    
    comparison_plot = create_comparison_plot(selected_files)
    
    if comparison_plot:
        return jsonify({'plot_html': comparison_plot})
    else:
        return jsonify({'error': 'Could not create comparison plot. Check if selected files have required columns.'}), 400

if __name__ == '__main__':
    app.run(debug=True)
