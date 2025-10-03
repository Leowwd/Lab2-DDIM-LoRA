#!/usr/bin/env python3
"""
Calculate FID scores and output to Excel table
"""
import os
import sys
import pandas as pd
from pathlib import Path

sys.path.append('./fid')
from measure_fid import calculate_fid_given_paths

# Configuration
reference_path = "./data/afhq/eval"  # Change this to your reference dataset path
samples_base_path = "./samples"

steps_list = [10, 20, 50, 100, 1000]
eta_list = [0, 0.2, 0.5, 1.0]

eta_to_folder = {
    0: "eta_0",
    0.2: "eta_02",
    0.5: "eta_05",
    1.0: "eta_1"
}

def main():
    print("=" * 80)
    print("FID Calculation Script")
    print("=" * 80)
    print(f"Reference path: {reference_path}")
    print(f"Samples path: {samples_base_path}")
    print(f"Steps: {steps_list}")
    print(f"Eta values: {eta_list}")
    print("=" * 80)
    
    # Check paths
    if not os.path.exists(samples_base_path):
        print(f"ERROR: Samples path not found: {samples_base_path}")
        return
    
    if not os.path.exists(reference_path):
        print(f"WARNING: Reference path not found: {reference_path}")
        print("Please update the reference_path in the script")
        user_input = input("Continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            return
    
    # Calculate FID scores
    results = []
    total_configs = len(steps_list) * len(eta_list)
    current = 0
    
    for steps in steps_list:
        for eta in eta_list:
            current += 1
            folder_name = f"steps_{steps}_{eta_to_folder[eta]}"
            sample_path = os.path.join(samples_base_path, folder_name)
            
            print(f"\n[{current}/{total_configs}] " + "=" * 60)
            print(f"Steps: {steps}, Eta: {eta}")
            print(f"Folder: {folder_name}")
            
            if not os.path.exists(sample_path):
                print(f"⚠️  Folder not found, skipping...")
                results.append({
                    'steps': steps,
                    'eta': eta,
                    'fid': None
                })
                continue
            
            try:
                fid_value = calculate_fid_given_paths(
                    [reference_path, sample_path],
                    img_size=256,
                    batch_size=64
                )
                print(f"✅ FID Score: {fid_value:.4f}")
                
                results.append({
                    'steps': steps,
                    'eta': eta,
                    'fid': fid_value
                })
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                results.append({
                    'steps': steps,
                    'eta': eta,
                    'fid': None
                })
    
    print("\n" + "=" * 80)
    print("✅ All calculations completed!")
    print("=" * 80)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Create pivot table
    pivot_table = df.pivot(index='steps', columns='eta', values='fid')
    pivot_table = pivot_table.sort_index()
    
    # Display table
    print("\n" + "=" * 80)
    print("FID SCORES TABLE")
    print("=" * 80)
    print(pivot_table.to_string())
    print("\n")
    
    # Save to Excel
    output_excel = "fid_results.xlsx"
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        # Save pivot table
        pivot_table.to_excel(writer, sheet_name='FID_Table')
        
        # Save raw data
        df.to_excel(writer, sheet_name='Raw_Data', index=False)
        
        # Create summary statistics
        summary = pd.DataFrame({
            'Metric': ['Best FID', 'Worst FID', 'Mean FID', 'Std FID'],
            'Value': [
                df['fid'].min(),
                df['fid'].max(),
                df['fid'].mean(),
                df['fid'].std()
            ]
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Average by eta
        avg_by_eta = df.groupby('eta')['fid'].mean().reset_index()
        avg_by_eta.columns = ['eta', 'avg_fid']
        avg_by_eta.to_excel(writer, sheet_name='Avg_by_Eta', index=False)
        
        # Average by steps
        avg_by_steps = df.groupby('steps')['fid'].mean().reset_index()
        avg_by_steps.columns = ['steps', 'avg_fid']
        avg_by_steps.to_excel(writer, sheet_name='Avg_by_Steps', index=False)
    
    print(f"✅ Excel file saved: {output_excel}")
    
    # Also save CSV
    output_csv = "fid_results.csv"
    pivot_table.to_csv(output_csv)
    print(f"✅ CSV file saved: {output_csv}")
    
    # Save formatted text table
    output_txt = "fid_results.txt"
    with open(output_txt, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("FID SCORES TABLE\n")
        f.write("=" * 80 + "\n\n")
        f.write(pivot_table.to_string())
        f.write("\n\n")
        f.write("=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        
        # Find best and worst
        best_idx = df['fid'].idxmin()
        best = df.loc[best_idx]
        worst_idx = df['fid'].idxmax()
        worst = df.loc[worst_idx]
        
        f.write(f"\nBest Configuration:\n")
        f.write(f"  Steps: {best['steps']}, Eta: {best['eta']}, FID: {best['fid']:.4f}\n")
        f.write(f"\nWorst Configuration:\n")
        f.write(f"  Steps: {worst['steps']}, Eta: {worst['eta']}, FID: {worst['fid']:.4f}\n")
        
        f.write(f"\nAverage FID by Eta:\n")
        for eta in eta_list:
            avg = df[df['eta'] == eta]['fid'].mean()
            f.write(f"  η={eta}: {avg:.4f}\n")
        
        f.write(f"\nAverage FID by Steps:\n")
        for steps in steps_list:
            avg = df[df['steps'] == steps]['fid'].mean()
            f.write(f"  {steps} steps: {avg:.4f}\n")
    
    print(f"✅ Text file saved: {output_txt}")
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    best_idx = df['fid'].idxmin()
    best = df.loc[best_idx]
    print(f"\n🏆 Best: Steps={best['steps']}, η={best['eta']}, FID={best['fid']:.4f}")
    
    worst_idx = df['fid'].idxmax()
    worst = df.loc[worst_idx]
    print(f"❌ Worst: Steps={worst['steps']}, η={worst['eta']}, FID={worst['fid']:.4f}")
    
    print(f"\n📈 Overall Mean FID: {df['fid'].mean():.4f}")
    print(f"📊 Overall Std FID: {df['fid'].std():.4f}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
