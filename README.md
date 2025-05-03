video-seo-optimizer/
├── .env
├── app.py
├── requirements.txt
├── README.md
│
├── utils/
│   ├── __init__.py
│   ├── video_extractor.py
│   ├── seo_agents.py
│   └── thumbnails.py
│
└── assets/
    └── logo.png



# 
mkdir -p video-seo-optimizer/utils video-seo-optimizer/assets
cd video-seo-optimizer
#
touch app.py
touch utils/video_extractor.py
touch utils/seo_agents.py
touch utils/thumbnails.py
touch assets/logo.png
touch README.md
touch ananlysi_functions.py

# 
pip install -r requirements.txt

#
streamlit run app.py



# for creatig environment

conda create -n lang6 python=3.11 -y

conda activate lang6

pip install -r requirements.txt