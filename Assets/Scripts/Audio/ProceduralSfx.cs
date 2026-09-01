using UnityEngine;

namespace DirtTrail
{
    /// <summary>
    /// The game has no recorded audio, so the few sounds it needs are synthesised
    /// once at startup and cached. A four-stroke single is mostly a buzzy
    /// sawtooth with a lumpy envelope, which is cheap to fake convincingly; the
    /// impacts are shaped noise.
    ///
    /// Everything is generated at a length that is a whole number of cycles, so
    /// the engine loop has no click at the seam.
    /// </summary>
    public static class ProceduralSfx
    {
        const int Rate = 44100;

        static AudioClip engine, land, wipeout, pickup, trick, nitro;

        public static AudioClip Engine => engine ??= BuildEngine();
        public static AudioClip Land => land ??= BuildLand();
        public static AudioClip Wipeout => wipeout ??= BuildWipeout();
        public static AudioClip Pickup => pickup ??= BuildPickup();
        public static AudioClip Trick => trick ??= BuildTrick();
        public static AudioClip Nitro => nitro ??= BuildNitro();

        static AudioClip Make(string name, float[] data)
        {
            var clip = AudioClip.Create(name, data.Length, 1, Rate, false);
            clip.SetData(data, 0);
            return clip;
        }

        static float Rand(ref uint state)
        {
            // xorshift, so the noise is identical every run
            state ^= state << 13;
            state ^= state >> 17;
            state ^= state << 5;
            return (state / (float)uint.MaxValue) * 2f - 1f;
        }

        /// <summary>One second of idle-ish engine at 80 Hz, built to loop.</summary>
        static AudioClip BuildEngine()
        {
            const float baseHz = 80f;
            int cycles = 80;
            int length = Mathf.RoundToInt(Rate * cycles / baseHz);
            var data = new float[length];
            uint seed = 0x5eed1234;

            float lowpass = 0f;
            for (int i = 0; i < length; i++)
            {
                float phase = (i * baseHz / Rate) % 1f;

                // sawtooth body plus its second harmonic, which is what gives a
                // single-cylinder its rasp rather than a smooth hum
                float saw = phase * 2f - 1f;
                float second = Mathf.Sin(phase * Mathf.PI * 4f) * 0.35f;

                // firing pulse: one hard event per revolution
                float pulse = phase < 0.12f ? (1f - phase / 0.12f) : 0f;

                float noise = Rand(ref seed) * 0.16f;
                lowpass += (noise - lowpass) * 0.25f;

                data[i] = (saw * 0.42f + second + pulse * 0.5f + lowpass) * 0.34f;
            }
            return Make("Engine", data);
        }

        static AudioClip BuildLand()
        {
            int length = Rate / 4;
            var data = new float[length];
            uint seed = 0x1a2b3c4d;
            float lp = 0f;

            for (int i = 0; i < length; i++)
            {
                float t = i / (float)length;
                float env = Mathf.Exp(-t * 16f);
                float noise = Rand(ref seed);
                lp += (noise - lp) * 0.09f;             // thud, not hiss
                float body = Mathf.Sin(i * 2f * Mathf.PI * 62f / Rate) * 0.5f;
                data[i] = (lp * 1.6f + body) * env * 0.7f;
            }
            return Make("Land", data);
        }

        static AudioClip BuildWipeout()
        {
            int length = (int)(Rate * 0.55f);
            var data = new float[length];
            uint seed = 0x77abc001;
            float lp = 0f;

            for (int i = 0; i < length; i++)
            {
                float t = i / (float)length;
                float env = Mathf.Exp(-t * 5.5f);
                float noise = Rand(ref seed);
                lp += (noise - lp) * (0.30f - t * 0.22f);   // opens up then closes down
                float scrape = Mathf.Sin(i * 2f * Mathf.PI * (150f - t * 90f) / Rate) * 0.3f;
                data[i] = (lp * 1.9f + scrape) * env * 0.8f;
            }
            return Make("Wipeout", data);
        }

        static AudioClip BuildPickup()
        {
            int length = (int)(Rate * 0.20f);
            var data = new float[length];
            for (int i = 0; i < length; i++)
            {
                float t = i / (float)length;
                float hz = t < 0.5f ? 520f : 780f;         // clean step, not a slide
                float env = Mathf.Exp(-t * 7f) * (1f - Mathf.Exp(-t * 90f));
                data[i] = Mathf.Sin(i * 2f * Mathf.PI * hz / Rate) * env * 0.42f;
            }
            return Make("Pickup", data);
        }

        static AudioClip BuildTrick()
        {
            int length = (int)(Rate * 0.16f);
            var data = new float[length];
            for (int i = 0; i < length; i++)
            {
                float t = i / (float)length;
                float env = Mathf.Exp(-t * 9f) * (1f - Mathf.Exp(-t * 120f));
                float hz = 660f + t * 240f;
                data[i] = (Mathf.Sin(i * 2f * Mathf.PI * hz / Rate) * 0.7f
                           + Mathf.Sin(i * 2f * Mathf.PI * hz * 1.5f / Rate) * 0.3f) * env * 0.36f;
            }
            return Make("Trick", data);
        }

        static AudioClip BuildNitro()
        {
            int length = (int)(Rate * 0.7f);
            var data = new float[length];
            uint seed = 0x2f8e11a3;
            float hp = 0f, last = 0f;

            for (int i = 0; i < length; i++)
            {
                float t = i / (float)length;
                float env = (1f - Mathf.Exp(-t * 40f)) * Mathf.Exp(-t * 3.4f);
                float noise = Rand(ref seed);
                hp = 0.86f * (hp + noise - last);            // hiss
                last = noise;
                data[i] = hp * env * 0.5f;
            }
            return Make("Nitro", data);
        }
    }
}
