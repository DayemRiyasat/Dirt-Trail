using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Two downward casts, one per axle. Gives grounded state, a usable surface
    /// normal and per-wheel ride height, which is what both the physics and the
    /// suspension visuals need. Replaces the single OverlapCircle, which could
    /// not tell a slope from a wall and had no normal to align to.
    /// </summary>
    public class GroundSensor : MonoBehaviour
    {
        [SerializeField] Transform rearAxle;
        [SerializeField] Transform frontAxle;

        [Tooltip("Wheel radius plus a little tolerance.")]
        [SerializeField] float probeLength = 0.72f;

        [Tooltip("How far past the wheel we still look, for suspension and landing assist.")]
        [SerializeField] float lookAhead = 2.6f;

        [Tooltip("Grace period after leaving the ground where throttle still bites.")]
        [SerializeField] float coyoteTime = 0.09f;

        float lastGroundedAt = -99f;

        public bool RearDown { get; private set; }
        public bool FrontDown { get; private set; }

        /// <summary>Either wheel touching. The strict test.</summary>
        public bool Grounded => RearDown || FrontDown;

        /// <summary>Grounded, or grounded recently enough that input should still count.</summary>
        public bool Effective => Grounded || Time.time - lastGroundedAt <= coyoteTime;

        /// <summary>Averaged surface normal, or world up when airborne.</summary>
        public Vector2 Normal { get; private set; } = Vector2.up;

        /// <summary>Unit vector along the slope, pointing the way the bike faces.</summary>
        public Vector2 Forward { get; private set; } = Vector2.right;

        /// <summary>Distance from the lower wheel to the ground, or a large number.</summary>
        public float Height { get; private set; } = 99f;

        /// <summary>Compression 0..1 per wheel, for the suspension visual.</summary>
        public float RearCompression { get; private set; }
        public float FrontCompression { get; private set; }

        public float AirTime { get; private set; }

        void Reset()
        {
            probeLength = 0.72f;
            lookAhead = 2.6f;
        }

        void FixedUpdate()
        {
            Vector2 down = -transform.up;
            var rear = Probe(rearAxle, down);
            var front = Probe(frontAxle, down);

            RearDown = rear.hit && rear.distance <= probeLength;
            FrontDown = front.hit && front.distance <= probeLength;

            RearCompression = Compression(rear);
            FrontCompression = Compression(front);

            Vector2 n = Vector2.zero;
            if (rear.hit) n += rear.normal;
            if (front.hit) n += front.normal;
            Normal = n.sqrMagnitude > 0.0001f ? n.normalized : Vector2.up;
            Forward = new Vector2(Normal.y, -Normal.x);
            if (Vector2.Dot(Forward, transform.right) < 0f) Forward = -Forward;

            Height = Mathf.Min(rear.hit ? rear.distance : 99f, front.hit ? front.distance : 99f);

            if (Grounded)
            {
                lastGroundedAt = Time.time;
                AirTime = 0f;
            }
            else
            {
                AirTime += Time.fixedDeltaTime;
            }
        }

        float Compression(Hit h)
        {
            if (!h.hit) return 0f;
            return Mathf.Clamp01(1f - h.distance / probeLength);
        }

        struct Hit
        {
            public bool hit;
            public float distance;
            public Vector2 normal;
        }

        Hit Probe(Transform axle, Vector2 down)
        {
            var result = new Hit { distance = 99f, normal = Vector2.up };
            if (axle == null) return result;

            var cast = Physics2D.Raycast(axle.position, down, lookAhead, GameLayers.GroundMask);
            if (!cast) return result;

            result.hit = true;
            result.distance = cast.distance;
            result.normal = cast.normal;
            return result;
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.yellow;
            foreach (var axle in new[] { rearAxle, frontAxle })
            {
                if (axle == null) continue;
                Gizmos.DrawLine(axle.position, axle.position - transform.up * probeLength);
            }
        }
    }
}
