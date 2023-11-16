from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoriesAPI)
router.register('posts', views.PostsAPI)
router.register('posts_recommended', views.PostsRecommended)

router.register('posts_r', views.GetRecommendation)
router.register('posts_instant', views.InstantRecommendation)
urlpatterns = [
    path('', include(router.urls)),
    path('create_recommendations', views.create_recommendations)
]
