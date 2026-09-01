using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// Drifts the menu camera sideways at a walking pace. The parallax rig and
    /// the ground strip both key off camera position, so this one line of motion
    /// is what makes the title screen feel like somewhere rather than a picture.
    /// </summary>
    public class SlowPan : MonoBehaviour
    {
        [Tooltip("World units per second. Slow enough that it never pulls focus.")]
        [SerializeField] float speed = 3.2f;

        void Update()
        {
            transform.position += Vector3.right * (speed * Time.unscaledDeltaTime);
        }
    }
}
