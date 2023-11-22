from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoriesAPI)
router.register('posts', views.PostsAPI)
router.register('posts_recommended', views.GetRecommendation)
router.register('new', views.NewPostAPI)
router.register('edit', views.EditPostAPI)
router.register('categories', views.CategoriesAPI, basename='categories')
router.register('favourites', views.FavouritesAPI)
router.register('like', views.LikeAPI)
router.register('liked', views.LikedAPI)
router.register('profiles', views.ProfileAPI)
router.register('my_profile', views.MyProfileAPI)
router.register('my_posts', views.MyPostsAPI)
router.register('notifications', views.NotificationsAPI)
urlpatterns = [
    path('', include(router.urls)),
    path('create_recommendations', views.create_recommendations_api),
    path('update_last_seen', views.update_last_seen)

]
