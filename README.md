# Emi Shop Backend
- Django Backend for Mobile Application
## Endpoints
<div style="display: flex;
    flex-wrap: wrap; 
    gap: 10px; 
    justify-content: center; 
    padding: 20px; ">
<img style="width: 100%;
    max-width: 200px;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    object-fit: contain;" src="https://raw.githubusercontent.com/Natan-Asrat/ecommerce_app_demo/main/screenshots/all.JPG" alt="detail post screenshot" height="550"/>
<img style="width: 100%;
    max-width: 200px;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    object-fit: contain;" src="https://raw.githubusercontent.com/Natan-Asrat/ecommerce_app_demo/main/screenshots/transactions.JPG" alt="detail post screenshot" height="550"/>
<img style="width: 100%;
    max-width: 200px;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    object-fit: contain;" src="https://raw.githubusercontent.com/Natan-Asrat/ecommerce_app_demo/main/screenshots/app.JPG" alt="detail post screenshot" height="550"/>
<img style="width: 100%;
    max-width: 200px;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    object-fit: contain;" src="https://raw.githubusercontent.com/Natan-Asrat/ecommerce_app_demo/main/screenshots/posts.JPG" alt="detail post screenshot" height="550"/>
</div>


## Recommendation System
<a href="https://github.com/Natan-Asrat/ecommerce_app_backend/blob/main/posts/queries.py#L169">View 775 lines of Code - Recommender</a>
- Utilized 6 separate recommenders:
  - Item-Item Collaborative Filtering: Find items similar to the items that the user liked or interacted with.
  - User-User Collaborative Filtering: Find items that other similar users liked or interacted with.
  - User-Category Collaborative Filtering: Find sellers and their items in categories that user liked or interacted with.
  - Following: Items that are sold by the user's following.
  - New Posts: New posts in the categories user has interacted with. This recommender helps new posts get reach if seller had no previous interaction yet.
  - Category: Unlike User-Category Collaborative Filtering, this recommender searches directly for items in a category and sort by amount of interactions they have.
- Ads are personalized by:
  - Categories user has interacted with.
  - If a user is viewing a product, similar ads are shown below.
  - If a user is viewing a category, ads in that category are shown.
  - For each 10 organic posts, there are 3 ads in feed.

## Routes
<a href="https://github.com/Natan-Asrat/ecommerce_app_backend/blob/main/posts/urls.py">View Definition of Routes - urls.py</a> | <a href="https://github.com/Natan-Asrat/ecommerce_app_backend/blob/main/posts/views.py">View Implementation of Routes - views.py</a>
- There are 46 API endpoints mainly for:
  - Post details, create new post, edit post, list a profile's posts ...
  - Categories list, posts in a category, ...
  - User Interaction (liking post, following users, viewing posts and profiles), ...
  - Transactions, Payment methods, Packages, ....
  - Boost posts for more reach, bidding prices, ...
  - Authentication, firebase related, ....

## Database Models
<a href="https://github.com/Natan-Asrat/ecommerce_app_backend/blob/main/posts/models.py">View Models</a>
- There are 18 database models for:
  - User Details, Followers, Notifications, Recommendations
  - Post Details, Favourite Posts, Liked Posts, Post Images, Seen Posts, Ads, Categories
  - Transactions, Payment Methods, Packages, 
  - Interactions (User-User, User-Category, User-Item, Category-Seller)
