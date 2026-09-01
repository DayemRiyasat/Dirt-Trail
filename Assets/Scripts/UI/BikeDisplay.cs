using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// A parked bike for the garage and the title screen. Same sprites and the
    /// same axle offsets as the playable bike, so what you pick is what you ride.
    /// </summary>
    public class BikeDisplay : MonoBehaviour
    {
        [SerializeField] SpriteRenderer body;
        [SerializeField] SpriteRenderer rider;
        [SerializeField] SpriteRenderer frontWheel;
        [SerializeField] SpriteRenderer rearWheel;

        [Header("Idle")]
        [Tooltip("Degrees the parked bike rocks through. Keep it nearly still.")]
        [SerializeField] float rockAmount = 0.8f;

        [SerializeField] float rockSpeed = 1.1f;
        [SerializeField] float wheelIdleSpin = 0f;

        Vector3 restEuler;

        void Awake() => restEuler = transform.localEulerAngles;

        public void Apply(BikeConfig config)
        {
            if (config == null) return;
            if (body != null) body.sprite = config.body;
            if (rider != null) rider.sprite = config.rider;
            if (frontWheel != null) frontWheel.sprite = config.wheelFront;
            if (rearWheel != null) rearWheel.sprite = config.wheelRear;
        }

        void Update()
        {
            float t = Time.unscaledTime;
            transform.localEulerAngles = restEuler +
                new Vector3(0f, 0f, Mathf.Sin(t * rockSpeed) * rockAmount);

            if (Mathf.Approximately(wheelIdleSpin, 0f)) return;
            float spin = -t * wheelIdleSpin;
            if (frontWheel != null)
                frontWheel.transform.localRotation = Quaternion.Euler(0f, 0f, spin);
            if (rearWheel != null)
                rearWheel.transform.localRotation = Quaternion.Euler(0f, 0f, spin);
        }
    }
}
