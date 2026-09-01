using System;
using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// A collectable sitting on the trail. Bobs gently, takes itself out of play
    /// on contact, and hands the whole config to the bike rather than poking at
    /// individual fields. No coroutine timer here: duration is the bike's
    /// problem, so a scene reload cannot leave a dangling effect.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Pickup : MonoBehaviour
    {
        [SerializeField] PickupConfig config;
        [SerializeField] SpriteRenderer icon;

        [Header("Idle motion")]
        [SerializeField] float bobHeight = 0.22f;
        [SerializeField] float bobSpeed = 1.7f;
        [SerializeField] float spin = 14f;

        /// <summary>Raised for the run manager: config, and where it happened.</summary>
        public static event Action<PickupConfig, Vector3> Collected;

        Vector3 origin;
        float phase;
        bool taken;

        void Reset()
        {
            var col = GetComponent<Collider2D>();
            if (col != null) col.isTrigger = true;
        }

        void Awake()
        {
            origin = transform.position;
            // Offset each pickup so a row of them does not pulse in lockstep.
            phase = (origin.x * 0.7f + origin.y * 1.3f) % Mathf.PI;

            if (icon == null) icon = GetComponentInChildren<SpriteRenderer>();
            if (icon != null && config != null)
            {
                if (config.icon != null) icon.sprite = config.icon;
                icon.color = Color.white;
            }
        }

        void Update()
        {
            if (taken) return;
            float t = Time.time * bobSpeed + phase;
            transform.position = origin + Vector3.up * (Mathf.Sin(t) * bobHeight);
            if (icon != null)
                icon.transform.localRotation =
                    Quaternion.Euler(0f, 0f, Mathf.Sin(t * 0.6f) * spin);
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (taken || config == null) return;
            if (!GameLayers.IsRider(other.gameObject.layer)) return;

            var bike = other.GetComponentInParent<BikeController>();
            if (bike == null || bike.IsWiped) return;

            taken = true;
            bike.GrantPowerup(config.kind, config.duration);
            Collected?.Invoke(config, transform.position);

            gameObject.SetActive(false);
        }
    }
}
