from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf.urls.static import static
from django.conf import settings
from rest_framework_nested import routers
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet, FCMDeviceViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = DefaultRouter()
router.register('posts', views.PostsAPI)
router.register('posts_anonymous', views.PostsAnonymousAPI)
router.register('posts_recommended', views.GetRecommendation)
router.register('new', views.NewPostAPI)
router.register('edit', views.EditPostAPI)
router.register('categories', views.CategoriesAPI, basename='categories')
router.register('categories_anonymous', views.CategoriesAnonymousAPI, basename='categories_anonymous')
router.register('categories_recommended', views.CategoriesRecommendedAPI, basename='categories_recommended')
router.register('favourites', views.FavouritesAPI)
router.register('like', views.LikeAPI)
router.register('follow', views.FollowAPI)
router.register('save', views.SaveAPI)
router.register('category', views.CategoryAPI)
router.register('liked', views.LikedAPI)
router.register('profiles', views.ProfileAPI)
router.register('profiles_anonymous', views.ProfileAnonymousAPI)
router.register('my_profile', views.MyProfileAPI)
router.register('my_posts', views.MyPostsAPI)
router.register('notifications', views.NotificationsAPI)
router.register('similar', views.SimilarPostsAPI)
router.register('create_ads', views.CreateAdsAPI)
router.register('packages', views.BuyPackagesAPI)
router.register('packages_anonymous', views.PackagesAnonymousAPI)
router.register('get_bids', views.GetBids)
router.register('get_payment_methods', views.GetPaymentMethods)
router.register('my_transactions', views.GetMyTransactions)
router.register('my_pending_transactions', views.GetMyPendingTransactions)
router.register('my_rejected_transactions', views.GetMyRejectedTransactions)
router.register('my_verified_transactions', views.GetMyVerifiedTransactions)
router.register('admin_pending_transactions', views.AdminPendingTransactions)
router.register('admin_rejected_transactions', views.AdminRejectedTransactions)
router.register('admin_verified_transactions', views.AdminVerifiedTransactions)
router.register('admin_recent_transactions', views.AdminRecentTransactions)
router.register('devices', FCMDeviceAuthorizedViewSet)

profile_router = routers.NestedDefaultRouter(router, 'profiles', lookup = 'seller')
profile_router.register('profile_posts', views.ProfilePostsAPI, basename='profile-posts')
urlpatterns = [
    path('', include(router.urls)),
    path('refresh', views.create_recommendations_api),
    path('update_last_seen', views.update_last_seen),
    path('check_is_user_new/<str:phone>/', views.check_if_user_is_new),
    path('update_user/', views.update_user),
    path('initial_categories/', views.initial_categories),
    path('send_verification_screenshot/', views.send_screenshot),
    path('verify_transaction/', views.transaction_verification_status),
    path('call_post/', views.call_post),
    path('notification_seen/', views.notification_seen),
    path('notification_button_pressed/', views.notification_button_pressed),
    path('call_profile/', views.call_profile),
    path('share_profile/', views.share_profile),
    path('share_post/', views.share_post),
    path('custom_otp_request/', views.custom_otp_request),
    path('custom_otp_verify/', views.custom_otp_verify),
    path('check_device_exists/', views.check_device_exists),
    path('logout', views.logout),
] + profile_router.urls

urlpatterns += [
    path('generate-receipt/<int:transaction_id>/', views.generate_receipt_pdf, name='generate_receipt_pdf'),
    path('schema/', SpectacularAPIView.as_view(), name='posts_app_schema'),
    path('schema/docs/', SpectacularSwaggerView.as_view(url_name='posts_app_schema')),
]