# --- Stage 1: build -------------------------------------------------------
# Χρειάζεται όλα τα devDependencies (TypeScript, Tailwind, ESLint, types).
FROM node:22-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Τα NEXT_PUBLIC_* ενσωματώνονται στο client bundle τη στιγμή του build, δεν
# διαβάζονται στο runtime — γι' αυτό περνάει ως build argument.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# --- Stage 2: runtime -----------------------------------------------------
# Ξεκινάει από καθαρό image και κρατάει μόνο production dependencies και το
# build output. Όλο το build toolchain του stage 1 μένει εκτός.
FROM node:22-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./

EXPOSE 3000

CMD ["npm", "start"]
