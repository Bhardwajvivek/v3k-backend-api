import requests

NEWS_API_KEY = "285b012f1f6644398cbe8bb09e710584"  # Replace with your NewsAPI key

def fetch_news(stock_name):
    url = f"https://newsapi.org/v2/everything?q={stock_name}&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"

    try:
        res = requests.get(url)
        data = res.json()
        
        if data.get("status") != "ok":
            return []

        headlines = []
        for article in data["articles"]:
            headlines.append({
                "title": article["title"],
                "url": article["url"],
                "source": article["source"]["name"],
                "time": article["publishedAt"]
            })

        return headlines

    except Exception as e:
        print(f"❌ Error fetching news for {stock_name}: {e}")
        return []
