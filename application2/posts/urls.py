from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('categories', views.CategoriesAPI)
router.register('posts', views.PostsAPI)
router.register('posts_IICF',views.PostsFromIICF_API)
router.register('posts_new',views.NewPostsAPI)
router.register('posts_UUCF',views.PostsFromUUCF_API)
router.register('posts_UCCF',views.PostsFromUCCF_API)
router.register('posts_category', views.PostsFromCategories)
router.register('posts_following', views.PostsFromFollowing)

router.register('posts_recommended', views.PostsRecommended)
urlpatterns = [
    path('', include(router.urls))
]
