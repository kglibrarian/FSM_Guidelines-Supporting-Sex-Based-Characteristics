"""
NORMALIZED CHECKPOINT SYSTEM for FSM Guidelines SABV Project - WITH PHASE 6
============================================================================
This script provides:
1. Standardized checkpoint directory structure
2. Cleanup function to remove old checkpoints before re-running
3. Phase 1, 2, 3, 4, AND 6 checkpoint implementation
4. Consistent checkpoint file naming across all phases
"""

import os
import pickle
import pandas as pd
import shutil
from datetime import datetime

# ==============================================================================
# STANDARDIZED CHECKPOINT CONFIGURATION
# ==============================================================================

# All checkpoints go in a single organized directory structure
CHECKPOINT_BASE_DIR = 'output/checkpoints'
CHECKPOINT_INTERVAL = 50  # Save every 50 items

# Phase-specific subdirectories
PHASE_DIRS = {
    'phase1_pubmed': os.path.join(CHECKPOINT_BASE_DIR, 'phase1_pubmed'),
    'phase2_crossref': os.path.join(CHECKPOINT_BASE_DIR, 'phase2_crossref'),
    'phase3_trials': os.path.join(CHECKPOINT_BASE_DIR, 'phase3_trials'),
    'phase4_ctgov': os.path.join(CHECKPOINT_BASE_DIR, 'phase4_ctgov'),
    'phase6_abstracts': os.path.join(CHECKPOINT_BASE_DIR, 'phase6_abstracts'),
    'phase7_analysis': os.path.join(CHECKPOINT_BASE_DIR, 'phase7_analysis')
}


# ==============================================================================
# CHECKPOINT CLEANUP FUNCTION - RUN BEFORE STARTING PIPELINE
# ==============================================================================

def cleanup_all_checkpoints(confirm=True):
    """
    Remove all checkpoint directories and start fresh.
    
    Parameters:
    -----------
    confirm : bool
        If True, requires manual confirmation before deleting
    """
    if os.path.exists(CHECKPOINT_BASE_DIR):
        if confirm:
            response = input(f"\n⚠️  Delete ALL checkpoints in {CHECKPOINT_BASE_DIR}? (yes/no): ")
            if response.lower() != 'yes':
                print("Checkpoint cleanup cancelled.")
                return False
        
        shutil.rmtree(CHECKPOINT_BASE_DIR)
        print(f"✓ All checkpoints deleted: {CHECKPOINT_BASE_DIR}")
        print("  Starting fresh - all checkpoint data removed\n")
        return True
    else:
        print(f"No checkpoint directory found at {CHECKPOINT_BASE_DIR}")
        print("Starting fresh - no cleanup needed\n")
        return True


def cleanup_phase_checkpoints(phase_name, confirm=True):
    """
    Remove checkpoints for a specific phase only.
    
    Parameters:
    -----------
    phase_name : str
        One of: 'phase1_pubmed', 'phase2_crossref', 'phase3_trials', 'phase4_ctgov', 'phase6_abstracts'
    confirm : bool
        If True, requires manual confirmation before deleting
    """
    if phase_name not in PHASE_DIRS:
        print(f"❌ Invalid phase name. Choose from: {list(PHASE_DIRS.keys())}")
        return False
    
    phase_dir = PHASE_DIRS[phase_name]
    
    if os.path.exists(phase_dir):
        if confirm:
            response = input(f"\n⚠️  Delete checkpoints for {phase_name}? (yes/no): ")
            if response.lower() != 'yes':
                print(f"Checkpoint cleanup cancelled for {phase_name}.")
                return False
        
        shutil.rmtree(phase_dir)
        print(f"✓ Checkpoints deleted for {phase_name}: {phase_dir}\n")
        return True
    else:
        print(f"No checkpoints found for {phase_name}")
        return True


# ==============================================================================
# PHASE 1: PUBMED DATA COLLECTION CHECKPOINTS
# ==============================================================================

def create_phase1_dirs():
    """Create Phase 1 checkpoint directory"""
    os.makedirs(PHASE_DIRS['phase1_pubmed'], exist_ok=True)


def save_phase1_checkpoint(batch_index, pubmed_data, failed_batches, total_count):
    """Save Phase 1 (PubMed) checkpoint"""
    create_phase1_dirs()
    
    checkpoint = {
        'batch_index': batch_index,
        'pubmed_data': pubmed_data,
        'failed_batches': failed_batches,
        'total_count': total_count,
        'timestamp': datetime.now().isoformat()
    }
    
    checkpoint_file = os.path.join(
        PHASE_DIRS['phase1_pubmed'], 
        f'phase1_checkpoint_batch_{batch_index:05d}.pkl'
    )
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint, f)
    
    # Also save as CSV for human readability
    if pubmed_data:
        csv_file = os.path.join(
            PHASE_DIRS['phase1_pubmed'],
            f'phase1_checkpoint_batch_{batch_index:05d}.csv'
        )
        pd.DataFrame(pubmed_data).to_csv(csv_file, index=False)


def load_phase1_checkpoint():
    """Load the latest Phase 1 checkpoint"""
    phase1_dir = PHASE_DIRS['phase1_pubmed']
    
    if not os.path.exists(phase1_dir):
        return None
    
    checkpoint_files = [
        f for f in os.listdir(phase1_dir) 
        if f.startswith('phase1_checkpoint_batch_') and f.endswith('.pkl')
    ]
    
    if not checkpoint_files:
        return None
    
    # Get the latest checkpoint by batch number
    latest_file = max(
        checkpoint_files,
        key=lambda x: int(x.replace('phase1_checkpoint_batch_', '').replace('.pkl', ''))
    )
    
    checkpoint_path = os.path.join(phase1_dir, latest_file)
    
    with open(checkpoint_path, 'rb') as f:
        checkpoint = pickle.load(f)
    
    print(f"\n📁 Loaded Phase 1 checkpoint:")
    print(f"   Batch: {checkpoint['batch_index']}")
    print(f"   Records: {len(checkpoint['pubmed_data']):,}")
    print(f"   Timestamp: {checkpoint['timestamp']}\n")
    
    return checkpoint


# ==============================================================================
# PHASE 2: CROSSREF REFERENCE COLLECTION CHECKPOINTS
# ==============================================================================

def create_phase2_dirs():
    """Create Phase 2 checkpoint directory"""
    os.makedirs(PHASE_DIRS['phase2_crossref'], exist_ok=True)


def save_phase2_checkpoint(last_idx, all_references, guidelines_without_refs):
    """Save Phase 2 (CrossRef) checkpoint"""
    create_phase2_dirs()
    
    checkpoint = {
        'last_idx': last_idx,
        'references': all_references,
        'no_refs': guidelines_without_refs,
        'timestamp': datetime.now().isoformat()
    }
    
    checkpoint_file = os.path.join(
        PHASE_DIRS['phase2_crossref'],
        f'phase2_checkpoint_guideline_{last_idx:05d}.pkl'
    )
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint, f)


def load_phase2_checkpoint():
    """Load the latest Phase 2 checkpoint"""
    phase2_dir = PHASE_DIRS['phase2_crossref']
    
    if not os.path.exists(phase2_dir):
        return None
    
    checkpoint_files = [
        f for f in os.listdir(phase2_dir)
        if f.startswith('phase2_checkpoint_guideline_') and f.endswith('.pkl')
    ]
    
    if not checkpoint_files:
        return None
    
    # Get the latest checkpoint
    latest_file = max(
        checkpoint_files,
        key=lambda x: int(x.replace('phase2_checkpoint_guideline_', '').replace('.pkl', ''))
    )
    
    checkpoint_path = os.path.join(phase2_dir, latest_file)
    
    with open(checkpoint_path, 'rb') as f:
        checkpoint = pickle.load(f)
    
    print(f"\n📁 Loaded Phase 2 checkpoint:")
    print(f"   Last guideline index: {checkpoint['last_idx']}")
    print(f"   References collected: {len(checkpoint['references']):,}")
    print(f"   Timestamp: {checkpoint['timestamp']}\n")
    
    return checkpoint


# ==============================================================================
# PHASE 3: CLINICAL TRIALS IDENTIFICATION CHECKPOINTS
# ==============================================================================

def create_phase3_dirs():
    """Create Phase 3 checkpoint directory"""
    os.makedirs(PHASE_DIRS['phase3_trials'], exist_ok=True)


def save_phase3_checkpoint(last_idx, trial_data, total_refs):
    """Save Phase 3 (Clinical Trials) checkpoint"""
    create_phase3_dirs()
    
    checkpoint = {
        'last_idx': last_idx,
        'trial_data': trial_data,
        'total_refs': total_refs,
        'timestamp': datetime.now().isoformat()
    }
    
    checkpoint_file = os.path.join(
        PHASE_DIRS['phase3_trials'],
        f'phase3_checkpoint_ref_{last_idx:05d}.pkl'
    )
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint, f)
    
    # Save progress CSV for monitoring
    if trial_data:
        csv_file = os.path.join(
            PHASE_DIRS['phase3_trials'],
            f'phase3_checkpoint_ref_{last_idx:05d}.csv'
        )
        pd.DataFrame(trial_data).to_csv(csv_file, index=False)


def load_phase3_checkpoint():
    """Load the latest Phase 3 checkpoint"""
    phase3_dir = PHASE_DIRS['phase3_trials']
    
    if not os.path.exists(phase3_dir):
        return None
    
    checkpoint_files = [
        f for f in os.listdir(phase3_dir)
        if f.startswith('phase3_checkpoint_ref_') and f.endswith('.pkl')
    ]
    
    if not checkpoint_files:
        return None
    
    # Get the latest checkpoint
    latest_file = max(
        checkpoint_files,
        key=lambda x: int(x.replace('phase3_checkpoint_ref_', '').replace('.pkl', ''))
    )
    
    checkpoint_path = os.path.join(phase3_dir, latest_file)
    
    with open(checkpoint_path, 'rb') as f:
        checkpoint = pickle.load(f)
    
    print(f"\n📁 Loaded Phase 3 checkpoint:")
    print(f"   Last reference index: {checkpoint['last_idx']:,}")
    print(f"   References processed: {len(checkpoint['trial_data']):,} / {checkpoint['total_refs']:,}")
    print(f"   Timestamp: {checkpoint['timestamp']}")
    
    # Count trials found so far
    trials_found = sum(1 for item in checkpoint['trial_data'] if item.get('is_clinical_trial'))
    nct_found = sum(1 for item in checkpoint['trial_data'] if item.get('nct_number'))
    print(f"   Clinical trials found: {trials_found:,}")
    print(f"   With NCT numbers: {nct_found:,}\n")
    
    return checkpoint


# ==============================================================================
# PHASE 4: CLINICALTRIALS.GOV DETAILS CHECKPOINTS
# ==============================================================================

def create_phase4_dirs():
    """Create Phase 4 checkpoint directory"""
    os.makedirs(PHASE_DIRS['phase4_ctgov'], exist_ok=True)


def save_phase4_checkpoint(last_idx, detailed_trials, total_trials):
    """Save Phase 4 (ClinicalTrials.gov) checkpoint"""
    create_phase4_dirs()
    
    checkpoint = {
        'last_idx': last_idx,
        'detailed_trials': detailed_trials,
        'total_trials': total_trials,
        'timestamp': datetime.now().isoformat()
    }
    
    checkpoint_file = os.path.join(
        PHASE_DIRS['phase4_ctgov'],
        f'phase4_checkpoint_trial_{last_idx:05d}.pkl'
    )
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint, f)
    
    # Save progress CSV for monitoring
    if detailed_trials:
        csv_file = os.path.join(
            PHASE_DIRS['phase4_ctgov'],
            f'phase4_checkpoint_trial_{last_idx:05d}.csv'
        )
        pd.DataFrame(detailed_trials).to_csv(csv_file, index=False)


def load_phase4_checkpoint():
    """Load the latest Phase 4 checkpoint"""
    phase4_dir = PHASE_DIRS['phase4_ctgov']
    
    if not os.path.exists(phase4_dir):
        return None
    
    checkpoint_files = [
        f for f in os.listdir(phase4_dir)
        if f.startswith('phase4_checkpoint_trial_') and f.endswith('.pkl')
    ]
    
    if not checkpoint_files:
        return None
    
    # Get the latest checkpoint
    latest_file = max(
        checkpoint_files,
        key=lambda x: int(x.replace('phase4_checkpoint_trial_', '').replace('.pkl', ''))
    )
    
    checkpoint_path = os.path.join(phase4_dir, latest_file)
    
    with open(checkpoint_path, 'rb') as f:
        checkpoint = pickle.load(f)
    
    print(f"\n📁 Loaded Phase 4 checkpoint:")
    print(f"   Last trial index: {checkpoint['last_idx']:,}")
    print(f"   Trials processed: {len(checkpoint['detailed_trials']):,} / {checkpoint['total_trials']:,}")
    print(f"   Timestamp: {checkpoint['timestamp']}")
    
    # Show some stats
    if checkpoint['detailed_trials']:
        with_enrollment = sum(1 for t in checkpoint['detailed_trials'] if t.get('enrollment'))
        with_sex = sum(1 for t in checkpoint['detailed_trials'] if t.get('sex'))
        print(f"   With enrollment data: {with_enrollment:,}")
        print(f"   With sex eligibility: {with_sex:,}\n")
    
    return checkpoint


# ==============================================================================
# PHASE 6: ARTICLE ABSTRACTS COLLECTION CHECKPOINTS 
# ==============================================================================

def create_phase6_dirs():
    """Create Phase 6 checkpoint directory"""
    os.makedirs(PHASE_DIRS['phase6_abstracts'], exist_ok=True)


def save_phase6_checkpoint(last_idx, abstracts_data, total_trials):
    """
    Save Phase 6 (Article Abstracts) checkpoint
    
    Parameters:
    -----------
    last_idx : int
        Index of last processed trial
    abstracts_data : list
        List of abstract dictionaries
    total_trials : int
        Total number of trials to process
    """
    create_phase6_dirs()
    
    checkpoint = {
        'last_idx': last_idx,
        'abstracts_data': abstracts_data,
        'total_trials': total_trials,
        'timestamp': datetime.now().isoformat()
    }
    
    checkpoint_file = os.path.join(
        PHASE_DIRS['phase6_abstracts'],
        f'phase6_checkpoint_abstract_{last_idx:05d}.pkl'
    )
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint, f)
    
    # Save progress CSV for monitoring
    if abstracts_data:
        csv_file = os.path.join(
            PHASE_DIRS['phase6_abstracts'],
            f'phase6_checkpoint_abstract_{last_idx:05d}.csv'
        )
        pd.DataFrame(abstracts_data).to_csv(csv_file, index=False)


def load_phase6_checkpoint():
    """Load the latest Phase 6 checkpoint"""
    phase6_dir = PHASE_DIRS['phase6_abstracts']
    
    if not os.path.exists(phase6_dir):
        return None
    
    checkpoint_files = [
        f for f in os.listdir(phase6_dir)
        if f.startswith('phase6_checkpoint_abstract_') and f.endswith('.pkl')
    ]
    
    if not checkpoint_files:
        return None
    
    # Get the latest checkpoint
    latest_file = max(
        checkpoint_files,
        key=lambda x: int(x.replace('phase6_checkpoint_abstract_', '').replace('.pkl', ''))
    )
    
    checkpoint_path = os.path.join(phase6_dir, latest_file)
    
    with open(checkpoint_path, 'rb') as f:
        checkpoint = pickle.load(f)
    
    print(f"\n📁 Loaded Phase 6 checkpoint:")
    print(f"   Last abstract index: {checkpoint['last_idx']:,}")
    print(f"   Abstracts processed: {len(checkpoint['abstracts_data']):,} / {checkpoint['total_trials']:,}")
    print(f"   Timestamp: {checkpoint['timestamp']}")
    
    # Show some stats
    if checkpoint['abstracts_data']:
        with_abstracts = sum(1 for a in checkpoint['abstracts_data'] if a.get('article_abstract'))
        with_titles = sum(1 for a in checkpoint['abstracts_data'] if a.get('article_title'))
        print(f"   With abstracts: {with_abstracts:,}")
        print(f"   With titles: {with_titles:,}\n")
    
    return checkpoint


# ==============================================================================
# PHASE 7: 
# ==============================================================================



# Add these two functions:
def create_phase7_dirs():
    """Create Phase 7 checkpoint directory"""
    os.makedirs(PHASE_DIRS['phase7_analysis'], exist_ok=True)

def save_phase7_checkpoint(last_idx, sex_analyses, total_trials):
    """Save Phase 7 (Sex Analysis) checkpoint"""
    create_phase7_dirs()
    checkpoint = {
        'last_idx': last_idx,
        'sex_analyses': sex_analyses,
        'total_trials': total_trials,
        'timestamp': datetime.now().isoformat()
    }
    checkpoint_file = os.path.join(
        PHASE_DIRS['phase7_analysis'],
        f'phase7_checkpoint_analysis_{last_idx:05d}.pkl'
    )
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint, f)
    
    if sex_analyses:
        csv_file = os.path.join(
            PHASE_DIRS['phase7_analysis'],
            f'phase7_checkpoint_analysis_{last_idx:05d}.csv'
        )
        pd.DataFrame(sex_analyses).to_csv(csv_file, index=False)

def load_phase7_checkpoint():
    """Load the latest Phase 7 checkpoint"""
    phase7_dir = PHASE_DIRS['phase7_analysis']
    if not os.path.exists(phase7_dir):
        return None
    checkpoint_files = [
        f for f in os.listdir(phase7_dir)
        if f.startswith('phase7_checkpoint_analysis_') and f.endswith('.pkl')
    ]
    if not checkpoint_files:
        return None
    latest_file = max(
        checkpoint_files,
        key=lambda x: int(x.replace('phase7_checkpoint_analysis_', '').replace('.pkl', ''))
    )
    checkpoint_path = os.path.join(phase7_dir, latest_file)
    with open(checkpoint_path, 'rb') as f:
        checkpoint = pickle.load(f)
    print(f"\n📁 Loaded Phase 7 checkpoint:")
    print(f"   Last analysis index: {checkpoint['last_idx']:,}")
    print(f"   Analyses processed: {len(checkpoint['sex_analyses']):,} / {checkpoint['total_trials']:,}")
    print(f"   Timestamp: {checkpoint['timestamp']}\n")
    return checkpoint
# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║    NORMALIZED CHECKPOINT SYSTEM FOR SABV GUIDELINES PROJECT - V3       ║
║                   NOW WITH PHASE 6 SUPPORT!                            ║
╚════════════════════════════════════════════════════════════════════════╝

CHECKPOINT DIRECTORY STRUCTURE:
--------------------------------
output/
└── checkpoints/
    ├── phase1_pubmed/
    │   ├── phase1_checkpoint_batch_00050.pkl
    │   └── phase1_checkpoint_batch_00050.csv
    │
    ├── phase2_crossref/
    │   └── phase2_checkpoint_guideline_00010.pkl
    │
    ├── phase3_trials/
    │   ├── phase3_checkpoint_ref_00050.pkl
    │   └── phase3_checkpoint_ref_00050.csv
    │
    ├── phase4_ctgov/
    │   ├── phase4_checkpoint_trial_00050.pkl
    │   └── phase4_checkpoint_trial_00050.csv
    │
    └── phase6_abstracts/ (NEW!)
        ├── phase6_checkpoint_abstract_00050.pkl
        └── phase6_checkpoint_abstract_00050.csv

PHASE 6 USAGE:
--------------
from normalized_checkpoint_system import (
    save_phase6_checkpoint,
    load_phase6_checkpoint,
    CHECKPOINT_INTERVAL
)

# Load checkpoint
checkpoint = load_phase6_checkpoint()
if checkpoint:
    abstracts_data = checkpoint['abstracts_data']
    start_idx = checkpoint['last_idx']
else:
    abstracts_data = []
    start_idx = 0

# Process trials
for idx in range(start_idx, total_trials):
    abstract_info = get_article_title_abstract(pmid)
    abstracts_data.append(abstract_info)
    
    if (idx + 1) % CHECKPOINT_INTERVAL == 0:
        save_phase6_checkpoint(idx + 1, abstracts_data, total_trials)
    """)
