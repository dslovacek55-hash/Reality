/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**.sreality.cz' },
      { protocol: 'https', hostname: '**.bezrealitky.cz' },
      { protocol: 'https', hostname: '**.bazos.cz' },
    ],
  },
};

module.exports = nextConfig;
