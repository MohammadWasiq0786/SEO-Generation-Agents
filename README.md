# SEO Generation Agents

![img1](https://github.com/MohammadWasiq0786/SEO-Generation-Agents/blob/main/images/01.png)

![img2](https://github.com/MohammadWasiq0786/SEO-Generation-Agents/blob/main/images/02.png)

![img3](https://github.com/MohammadWasiq0786/SEO-Generation-Agents/blob/main/images/03.png)

![img4](https://github.com/MohammadWasiq0786/SEO-Generation-Agents/blob/main/images/04.png)

![img5](https://github.com/MohammadWasiq0786/SEO-Generation-Agents/blob/main/images/05.png)

![img6](https://github.com/MohammadWasiq0786/SEO-Generation-Agents/blob/main/images/06.png)

![img7](https://github.com/MohammadWasiq0786/SEO-Generation-Agents/blob/main/images/07.png)


## Project Structure
```text
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

```

### Make Directory
```bash
mkdir -p video-seo-optimizer/utils video-seo-optimizer/assets
cd video-seo-optimizer

### Create Files/Folder
touch app.py
touch utils/video_extractor.py
touch utils/seo_agents.py
touch utils/thumbnails.py
touch assets/logo.png
touch README.md
touch ananlysi_functions.py
```

### Install `requirements.txt`
```bash
pip install -r requirements.txt
```

### Run App
```bash
streamlit run app.py
```


### For creatig environment

```bash
conda create -n seo python=3.11 -y

conda activate seo
```
