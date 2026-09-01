using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Particle systems are built here rather than authored in a prefab. Every
    /// number that matters is visible in one screen of code, which is worth more
    /// than inspector convenience for effects this small.
    /// </summary>
    public static class ParticleFactory
    {
        static Material spriteMaterial;

        static Material MaterialFor(Sprite sprite)
        {
            if (spriteMaterial == null)
            {
                var shader = Shader.Find("Sprites/Default");
                spriteMaterial = new Material(shader) { name = "Dirt FX" };
            }
            var mat = new Material(spriteMaterial);
            if (sprite != null && sprite.texture != null) mat.mainTexture = sprite.texture;
            return mat;
        }

        static ParticleSystem Create(string name, Transform parent, Sprite sprite,
                                     int sortingOrder)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);

            var ps = go.AddComponent<ParticleSystem>();
            var renderer = go.GetComponent<ParticleSystemRenderer>();
            renderer.material = MaterialFor(sprite);
            renderer.sortingOrder = sortingOrder;
            renderer.alignment = ParticleSystemRenderSpace.View;

            var main = ps.main;
            main.playOnAwake = false;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.scalingMode = ParticleSystemScalingMode.Hierarchy;

            var emission = ps.emission;
            emission.rateOverTime = 0f;
            return ps;
        }

        /// <summary>The trail off the rear wheel: slow, soft, fading upward.</summary>
        public static ParticleSystem Dust(Transform parent, Color tint)
        {
            var kit = FxKit.Load();
            var ps = Create("Dust", parent, kit != null ? kit.dust : null, -1);

            var main = ps.main;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.55f, 1.25f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.6f, 2.2f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.45f, 1.35f);
            main.startColor = tint;
            main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
            main.gravityModifier = -0.06f;          // dust hangs and drifts up
            main.maxParticles = 220;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 26f;
            shape.radius = 0.18f;
            shape.rotation = new Vector3(0f, 90f, 0f);   // spray backwards

            Fade(ps, 0.85f);
            Grow(ps, 1f, 2.4f);
            Drag(ps, 1.4f);
            return ps;
        }

        /// <summary>Roost: heavy clods thrown out on impact and under power.</summary>
        public static ParticleSystem Clods(Transform parent, Color tint)
        {
            var kit = FxKit.Load();
            var ps = Create("Clods", parent, kit != null ? kit.clod : null, 1);

            var main = ps.main;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.4f, 0.95f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(3f, 9f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.12f, 0.34f);
            main.startColor = tint * 0.75f;
            main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
            main.gravityModifier = 2.4f;
            main.maxParticles = 120;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 42f;
            shape.radius = 0.1f;
            shape.rotation = new Vector3(0f, 90f, 0f);

            var rotation = ps.rotationOverLifetime;
            rotation.enabled = true;
            rotation.z = new ParticleSystem.MinMaxCurve(-6f, 6f);
            return ps;
        }

        /// <summary>Nitro: a tight hot plume out the back, only while burning.</summary>
        public static ParticleSystem NitroFlare(Transform parent)
        {
            var kit = FxKit.Load();
            var ps = Create("Nitro", parent, kit != null ? kit.dust : null, 2);

            var main = ps.main;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.18f, 0.4f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(4f, 8f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.3f, 0.7f);
            main.startColor = new Color(1f, 0.72f, 0.34f, 1f);
            main.gravityModifier = -0.2f;
            main.maxParticles = 90;

            var emission = ps.emission;
            emission.rateOverTime = 55f;

            var shape = ps.shape;
            shape.enabled = true;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 12f;
            shape.radius = 0.06f;
            shape.rotation = new Vector3(0f, 90f, 0f);

            Fade(ps, 0.5f);
            return ps;
        }

        // ---- shared modules ------------------------------------------------
        static void Fade(ParticleSystem ps, float holdUntil)
        {
            var col = ps.colorOverLifetime;
            col.enabled = true;
            var gradient = new Gradient();
            gradient.SetKeys(
                new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                new[]
                {
                    new GradientAlphaKey(0f, 0f),
                    new GradientAlphaKey(1f, 0.12f),
                    new GradientAlphaKey(0.9f, holdUntil),
                    new GradientAlphaKey(0f, 1f),
                });
            col.color = new ParticleSystem.MinMaxGradient(gradient);
        }

        static void Grow(ParticleSystem ps, float from, float to)
        {
            var size = ps.sizeOverLifetime;
            size.enabled = true;
            var curve = new AnimationCurve(new Keyframe(0f, from), new Keyframe(1f, to));
            size.size = new ParticleSystem.MinMaxCurve(1f, curve);
        }

        static void Drag(ParticleSystem ps, float drag)
        {
            var limit = ps.limitVelocityOverLifetime;
            limit.enabled = true;
            limit.dampen = 0.12f;
            limit.limit = new ParticleSystem.MinMaxCurve(drag);
        }
    }
}
