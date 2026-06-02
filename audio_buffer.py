import numpy as np
import threading


class AudioRingBuffer:

    def __init__(self, sample_rate=16000, window_sec=4.0):

        self.sample_rate = sample_rate
        self.window_sec = window_sec

        # Total samples buffer can hold
        self.max_samples = int(sample_rate * window_sec)

        # Actual circular memory
        self.buffer = np.zeros(
            self.max_samples,
            dtype=np.float32
        )

        # Next write location
        self.write_pos = 0

        # Total lifetime samples received
        # (absolute audio timeline)
        self.total_samples_written = 0

        # Has buffer wrapped at least once?
        self.filled = False

        # Thread-safe lock
        self.lock = threading.RLock()

        print(
            f"📊 AudioRingBuffer initialized: "
            f"{window_sec}s window = "
            f"{self.max_samples} samples"
        )

    # =========================================================
    # APPEND AUDIO
    # =========================================================

    def append(self, samples: np.ndarray):

        with self.lock:

            num_samples = len(samples)

            was_filled = self.filled

            # -------------------------------------------------
            # CASE 1
            # Incoming chunk larger than whole buffer
            # -------------------------------------------------

            if num_samples >= self.max_samples:

                # Keep ONLY latest part
                self.buffer[:] = samples[-self.max_samples:]

                self.write_pos = 0
                self.filled = True

                self.total_samples_written += num_samples

                if not was_filled:
                    print(
                        f"✅ Buffer filled! "
                        f"(large chunk: {num_samples} samples)"
                    )

                return

            # -------------------------------------------------
            # CASE 2
            # Normal append
            # -------------------------------------------------

            end_pos = self.write_pos + num_samples

            # -------------------------------------------------
            # CASE 2A
            # No wrap-around
            # -------------------------------------------------

            if end_pos <= self.max_samples:

                self.buffer[
                    self.write_pos:end_pos
                ] = samples

            # -------------------------------------------------
            # CASE 2B
            # Wrap-around
            # -------------------------------------------------

            else:

                first = self.max_samples - self.write_pos

                # Fill end of buffer
                self.buffer[self.write_pos:] = samples[:first]

                # Continue from beginning
                self.buffer[:num_samples - first] = samples[first:]

                self.filled = True

                if not was_filled:
                    print("✅ Buffer filled! (wrapped around)")

            # Circular pointer update
            self.write_pos = end_pos % self.max_samples

            # Mark filled if we crossed capacity
            if (
                not self.filled
                and self.total_samples_written + num_samples >= self.max_samples
            ):
                self.filled = True

                if not was_filled:
                    print("✅ Buffer fully initialized")

            # Absolute timeline update
            self.total_samples_written += num_samples

    # =========================================================
    # GET FULL CHRONOLOGICAL AUDIO
    # =========================================================

    def get_audio(self):

        with self.lock:

            # Buffer not fully wrapped yet
            if not self.filled:

                return self.buffer[:self.write_pos].copy()

            # Reconstruct chronological order
            return np.concatenate((
                self.buffer[self.write_pos:],
                self.buffer[:self.write_pos]
            ))

    # =========================================================
    # GET EXACT TIMELINE CHUNK
    # =========================================================

    def get_chunk(self, start_sample, size):

        with self.lock:

            # Latest timeline position
            current_end = self.total_samples_written

            # Oldest audio still available
            current_start = max(
                0,
                current_end - self.max_samples
            )

            # Requested chunk end
            requested_end = start_sample + size

            # -------------------------------------------------
            # CASE 1
            # Requested audio already overwritten
            # -------------------------------------------------

            if start_sample < current_start:

                print(
                    "⚠️ Requested chunk already overwritten "
                    f"({start_sample} < {current_start})"
                )

                return None

            # -------------------------------------------------
            # CASE 2
            # Future audio not arrived yet
            # -------------------------------------------------

            if requested_end > current_end:

                return None

            # Get chronological audio
            audio = self.get_audio()

            # Convert absolute timeline
            # → relative array position
            relative_start = start_sample - current_start

            # Return exact chunk
            return audio[
                relative_start:
                relative_start + size
            ].copy()

    # =========================================================
    # DEBUG INFO
    # =========================================================

    def debug_info(self):

        with self.lock:

            current_end = self.total_samples_written

            current_start = max(
                0,
                current_end - self.max_samples
            )

            return {
                "write_pos": self.write_pos,
                "filled": self.filled,
                "total_samples_written": self.total_samples_written,
                "buffer_start": current_start,
                "buffer_end": current_end,
                "buffer_duration_sec":
                    self.max_samples / self.sample_rate
            }