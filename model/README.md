## Used car price prediction


### Project objective

Predict the price of a used car using the following features:
- make
- model
- manufacturing year
- gearbox
- fuel type
- mileage (km)
- engine capacity (cm3)
- engine power (CP)
- body type
- transmission
- pollution standard
- color
- price (target feature)

#### Motivation

Support buyers and sellers in making informed decisions based on data from existing **used** car listings found on [autovit.ro](https://www.autovit.ro/).


### Data collection

#### Virtual environment setup
```properties
cd extraction
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Running the data collection script
```properties
python3 scraper.py
```

#### Method
Built a web scraper (in `extraction/scraper.py`) to extract **used** car listings data from [https://www.autovit.ro/autoturisme/second](https://www.autovit.ro/autoturisme/second).

- only collected listings with values for all the selected features

