from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoriesAPI)
router.register('posts', views.PostsAPI)
router.register('posts_recommended', views.GetRecommendation)
router.register('new', views.NewPostAPI)
router.register('edit', views.EditPostAPI)

router.register('like', views.LikeAPI)
urlpatterns = [
    path('', include(router.urls)),
    path('create_recommendations', views.create_recommendations_api)
]
