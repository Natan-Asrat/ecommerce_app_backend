from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf.urls.static import static
from django.conf import settings
from rest_framework_nested import routers

router = DefaultRouter()
router.register('categories', views.CategoriesAPI)
router.register('posts', views.PostsAPI)
router.register('posts_recommended', views.GetRecommendation)
router.register('new', views.NewPostAPI)
router.register('edit', views.EditPostAPI)
router.register('categories', views.CategoriesAPI, basename='categories')
router.register('favourites', views.FavouritesAPI)
router.register('like', views.LikeAPI)
router.register('category', views.CategoryAPI)
router.register('liked', views.LikedAPI)
router.register('profiles', views.ProfileAPI)
router.register('my_profile', views.MyProfileAPI)
router.register('my_posts', views.MyPostsAPI)
router.register('notifications', views.NotificationsAPI)
router.register('similar', views.SimilarPostsAPI)

profile_router = routers.NestedDefaultRouter(router, 'profiles', lookup = 'seller')
profile_router.register('profile_posts', views.ProfilePostsAPI, basename='profile-posts')
urlpatterns = [
    path('', include(router.urls)),
    path('refresh', views.create_recommendations_api),
    path('update_last_seen', views.update_last_seen)
] + profile_router.urls