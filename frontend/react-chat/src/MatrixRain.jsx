import { useEffect, useRef } from 'react';

function MatrixRain() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // DevOps-themed characters
    const devopsChars = 'kubectl docker pod node deploy svc ingress helm yaml k8s container image registry namespace configmap secret volume pvc cronjob daemon replica rollout scale logs exec apply delete get describe patch 01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
    const chars = devopsChars.split('');

    let columns;
    let drops;
    let fontSize = 14;

    const initCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      columns = Math.floor(canvas.width / fontSize);
      drops = Array(columns).fill(1).map(() => Math.random() * -100);
    };

    initCanvas();

    const draw = () => {
      // Semi-transparent black to create fade trail
      ctx.fillStyle = 'rgba(1, 4, 9, 0.06)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < drops.length; i++) {
        const char = chars[Math.floor(Math.random() * chars.length)];

        // Vary the green color for depth effect
        const brightness = Math.random();
        if (brightness > 0.95) {
          // Bright white flash (head of the stream)
          ctx.fillStyle = '#ffffff';
          ctx.shadowColor = '#22c55e';
          ctx.shadowBlur = 15;
        } else if (brightness > 0.85) {
          ctx.fillStyle = '#4ade80'; // Bright green
          ctx.shadowColor = '#4ade80';
          ctx.shadowBlur = 10;
        } else if (brightness > 0.7) {
          ctx.fillStyle = '#22d3ee'; // Cyan accent
          ctx.shadowColor = '#22d3ee';
          ctx.shadowBlur = 6;
        } else if (brightness > 0.5) {
          ctx.fillStyle = '#06762fff'; // Classic Matrix green
          ctx.shadowBlur = 0;
        } else if (brightness > 0.3) {
          ctx.fillStyle = '#0ea5e9'; // Blue
          ctx.shadowBlur = 0;
        } else {
          ctx.fillStyle = 'rgba(34, 197, 94, 0.3)'; // Dim green
          ctx.shadowBlur = 0;
        }

        ctx.font = `${fontSize}px 'JetBrains Mono', monospace`;
        ctx.fillText(char, i * fontSize, drops[i] * fontSize);

        // Reset shadow
        ctx.shadowBlur = 0;

        // Reset drop to top with random delay
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i] += Math.random() * 0.5 + 0.3;
      }
    };

    const interval = setInterval(draw, 45);

    const handleResize = () => {
      initCanvas();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="matrix-canvas"
    />
  );
}

export default MatrixRain;
