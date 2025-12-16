customer-shopping-data-mining/
│
├── README.md                          # Tổng quan project
├── requirements.txt                   # Dependencies
├── data/
│   ├── raw/                          # Data gốc
│   │   └── customer_shopping_data.csv 
│   └── processed/                    # Data đã xử lý
│       └── cleaned_data.csv
│
├── 01_data_preprocessing/
│   ├── data_preprocessing.ipynb
│   ├── data_cleaning.py
│   ├── preprocessing_report.md
│   └── figures/
│
├── 02_eda_clustering/
│   ├── eda_analysis.ipynb
│   ├── clustering_analysis.ipynb
│   ├── clustering_models.py
│   ├── eda_clustering_report.md
│   └── figures/
│
├── 03_association_rules/
│   ├── association_rules.ipynb
│   ├── market_basket_analysis.py
│   ├── rules_results.csv
│   ├── association_rules_report.md
│   └── figures/
│
├── 04_classification_integration/
│   ├── classification_models.ipynb
│   ├── model_comparison.py
│   ├── final_report.ipynb
│   ├── classification_report.md
│   └── figures/
│
├── final_report/
│   ├── final_report.pdf
│   ├── presentation.pptx
│   └── summary.md
│
└── utils/
    ├── data_loader.py
    ├── visualization.py
    └── evaluation_metrics.py
