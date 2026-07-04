# Onboarding de perfil dinámico (sexo/talla) + registro limpio

**Fecha:** 2026-07-04
**Repos:** `ZAFIRA-CORE` (Django backend) · `zafira` (Flutter, `C:\FAZQ\DEV\MOBILE\MULTIPLATFORM\zafira`)

## Problema
El registro pide sexo (`gender`) y talla (`preferred_size`). Se quiere sacar eso del registro y pedirlo
después del login mediante un wizard de pantallas deslizables con buen diseño, extensible a más datos.
La "API del principio" (login + `/profile/me/`) debe indicar si esas pantallas se muestran; una vez
completado el perfil, no se muestran nunca más.

## Contrato de API (nuevo)
`User.to_json_api()` añade:
```json
"onboarding": { "completed": false, "pending_steps": ["gender", "preferred_size"] }
```
- `completed = mobile_profile.onboarding_completed OR (pending_steps está vacío)`.
- `pending_steps` = subconjunto ordenado de `("gender", "preferred_size")` cuyo dato falta
  (`gender` en `("", "no_indica")`, `preferred_size` vacío).
- Viaja en la respuesta de `POST /api/v1/auth/token/` y `GET /api/v1/auth/profile/me/`.
- Se persiste con el endpoint existente `PATCH /api/v1/auth/profile/update/`, que ahora acepta
  `onboarding_completed`.

## Backend — ZAFIRA-CORE
1. `core/profiles/models/profile.py` · `MobileProfile`: campo `onboarding_completed` (Boolean, default False)
   + `ONBOARDING_STEPS` + `onboarding_pending_steps()` + `onboarding_status()`.
2. `core/auth/models/user.py` · `to_json_api()`: añade clave `onboarding` (fallback si no hay perfil).
3. `core/user/api/v1/user/serializer/user.py` · `UserCreateSerializerInput`: elimina `gender` y
   `preferred_size` (campos + uso en `create()`); quedan con defaults del modelo. Quita import `GenderChoices`.
4. `core/auth/api/v1/auth/serializer/user.py` · `MobileProfileUpdateSerializer`: acepta y guarda
   `onboarding_completed`.
5. Migración de `profiles`.
6. Tests: registro no persiste sexo/talla; `to_json_api` trae `onboarding` con lógica de `completed`
   correcta; update marca completado.

## Frontend — zafira (Flutter, Clean Arch por feature)
1. `feature/auth/domain/register_request.dart`: quita `gender`/`preferredSize`.
2. `feature/auth/view/widgets/register/register_form.dart`: quita `GenderSelector` + campo talla y su
   estado/validación. (`gender_selector.dart` se conserva: lo usa `edit_profile_screen`.)
3. `feature/auth/domain/onboarding_info.dart` (freezed) + `user_model.dart`: campo `onboarding`.
4. Nueva feature `feature/onboarding/`:
   - `domain/onboarding_step.dart` (enum + metadata extensible).
   - `view/state/onboarding_state.dart`, `view/controller/onboarding_controller.dart`
     (índice de página + respuestas; persiste vía `authController.updateProfile`).
   - `view/main/onboarding_screen.dart` (PageView horizontal + progreso + botones).
   - `view/widgets/`: `onboarding_scaffold.dart`, `onboarding_progress.dart`,
     `onboarding_step_shell.dart`, `onboarding_option_grid.dart` (single-select reutilizable),
     `gender_step.dart`, `size_step.dart`.
5. `modules/common/routes/app_router.dart`: ruta `/onboarding`.
6. Gating: `splash_screen.dart` y `login_auth_mixin.dart` → `needsOnboarding(user) ? Onboarding : Home`.
7. `build_runner` (freezed/json) + `flutter analyze`.

## Reglas
- Cada archivo ≤ 300-400 líneas; widgets reutilizables; sin comentarios obvios.
- Tema ZAFIRA night: `authBackground`, `gradientPrimary`, chips `nightInput`/`nightBorder`, `AppGradientButton`.
- Reutilizar `updateProfile` y `/profile/me/`; nada de endpoints nuevos.

## Flujo
Registro (sin sexo/talla) → login → `onboarding.completed=false` → wizard (género → talla) → guarda +
marca completado → Home. Reapertura: `/profile/me/` `completed=true` → Home directo, sin wizard.
