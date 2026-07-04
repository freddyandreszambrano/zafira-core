from core.profiles.models import MobileProfile


class MobileProfileApi:
    def __init__(self, user):
        self.user = user

    def update_avatar(self, image):
        self.user.image = image
        self.user.save(update_fields=["image"])
        return self.user

    def update_profile(self, data):
        self.user.first_name = data.get("first_name", self.user.first_name)
        self.user.last_name = data.get("last_name", self.user.last_name)
        self.user.save(update_fields=["first_name", "last_name"])

        mobile_profile, _ = MobileProfile.objects.get_or_create(user=self.user)
        mobile_profile.gender = data.get("gender", mobile_profile.gender)
        mobile_profile.country = data.get("country", mobile_profile.country)
        mobile_profile.preferred_size = data.get("preferred_size", mobile_profile.preferred_size)
        mobile_profile.language = data.get("language", mobile_profile.language)
        mobile_profile.onboarding_completed = data.get(
            "onboarding_completed", mobile_profile.onboarding_completed
        )
        mobile_profile.onboarding_force_show = data.get(
            "onboarding_force_show", mobile_profile.onboarding_force_show
        )
        if data.get("onboarding_completed") is True:
            mobile_profile.onboarding_force_show = False
        if "style_preferences" in data:
            mobile_profile.style_preferences = data["style_preferences"]
        mobile_profile.save()
        self.user.mobile_profile = mobile_profile
        return self.user

    def delete_avatar(self):
        if self.user.image:
            self.user.image.delete(save=False)
            self.user.image = None
            self.user.save(update_fields=["image"])
        return self.user

    def update_try_on_photo(self, image):
        mobile_profile, _ = MobileProfile.objects.get_or_create(user=self.user)
        mobile_profile.try_on_photo = image
        mobile_profile.save(update_fields=["try_on_photo"])
        return self.user

    def delete_try_on_photo(self):
        mobile_profile = getattr(self.user, "mobile_profile", None)
        if mobile_profile and mobile_profile.try_on_photo:
            mobile_profile.try_on_photo.delete(save=False)
            mobile_profile.try_on_photo = None
            mobile_profile.save(update_fields=["try_on_photo"])
        return self.user
