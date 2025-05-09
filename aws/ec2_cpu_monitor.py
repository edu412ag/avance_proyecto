#!/usr/bin/env python3
"""
AWS EC2 CPU Monitor - Ready for Your Instance (i-0af43ba679fcca4fd in us-east-1)
"""

import pandas as pd
import matplotlib.pyplot as plt
import boto3
from datetime import datetime, timedelta
import warnings

# ========== PRE-CONFIGURED SETTINGS ==========
INSTANCE_ID = 'i-0af43ba679fcca4fd'  # Your instance
AWS_REGION = 'us-east-1'             # Your region
# ============================================

warnings.filterwarnings('ignore')

def fetch_cpu_data():
    """Fetches CPU metrics for your specific instance"""
    try:
        cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
        time_now = datetime.utcnow()
        
        print(f"\n📈 Getting CPU data for your instance {INSTANCE_ID}...")
        metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': INSTANCE_ID}],
            StartTime=time_now - timedelta(hours=1),
            EndTime=time_now,
            Period=300,  # 5-minute intervals
            Statistics=['Average', 'Maximum']
        )
        return metrics['Datapoints']
    
    except Exception as e:
        print(f"\n⚠️ Error: {str(e)}")
        print("Please verify:")
        print(f"1. Instance {INSTANCE_ID} exists in {AWS_REGION}")
        print("2. You have CloudWatch read permissions")
        print("3. AWS credentials are configured")
        return None

def create_cpu_plot(metrics):
    """Creates a customized CPU usage plot"""
    if not metrics:
        return

    df = pd.DataFrame(metrics).sort_values('Timestamp')
    df['Time'] = pd.to_datetime(df['Timestamp']).dt.strftime('%H:%M')

    plt.style.use('ggplot')
    plt.figure(figsize=(12, 6))
    
    # Main plot lines
    plt.plot(df['Time'], df['Average'], 
             marker='o', color='#3498db', 
             label='Average', linewidth=2)
    
    if 'Maximum' in df.columns:
        plt.plot(df['Time'], df['Maximum'], 
                 marker='^', color='#e74c3c', 
                 linestyle=':', label='Peak')

    # Threshold lines
    plt.axhline(80, color='red', linestyle='--', alpha=0.5, label='Critical (80%)')
    plt.axhline(60, color='orange', linestyle=':', alpha=0.3, label='Warning (60%)')

    # Plot customization
    plt.title(f'CPU Usage - Instance {INSTANCE_ID[:10]}...\nRegion: {AWS_REGION}', 
              fontsize=14, pad=15)
    plt.xlabel('Time (UTC)', fontsize=11)
    plt.ylabel('CPU Utilization (%)', fontsize=11)
    plt.ylim(0, 100)
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Save and show
    filename = f'cpu_{INSTANCE_ID[:8]}.png'
    plt.savefig(filename, dpi=120, bbox_inches='tight')
    print(f"\n✅ Plot saved as '{filename}'")
    plt.show()

if __name__ == "__main__":
    print(f"\n🖥️ AWS EC2 CPU Monitor - Instance: {INSTANCE_ID}")
    print("="*50)
    
    cpu_data = fetch_cpu_data()
    
    if cpu_data:
        create_cpu_plot(cpu_data)
    else:
        print("\nFailed to get data. Please check the errors above.")