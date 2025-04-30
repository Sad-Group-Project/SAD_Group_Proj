interface CacheItem<T> {
  data: T;
  timestamp: number;
}

interface CacheOptions {
  ttl?: number;
}

class CacheService {
  private cache: Map<string, CacheItem<any>> = new Map();
  private defaultTtl = 15 * 60 * 1000; // 15 minutes in milliseconds

  /**
   * Get data from cache if it exists and is not expired
   * @param key - The cache key
   * @param options - Cache options
   * @returns The cached data or null if not found or expired
   */
  get<T>(key: string, options?: CacheOptions): T | null {
    const item = this.cache.get(key);
    if (!item) return null;

    const ttl = options?.ttl || this.defaultTtl;
    const now = Date.now();
    
    if (now - item.timestamp > ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  /**
   * Store data in cache
   * @param key - The cache key
   * @param data - The data to store
   */
  set<T>(key: string, data: T): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  /**
   * Remove item from cache
   * @param key - The cache key
   */
  remove(key: string): void {
    this.cache.delete(key);
  }

  /**
   * Clear all cached items
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Invalidate a specific cache entry
   * @param key - The cache key to invalidate
   */
  invalidate(key: string): void {
    this.cache.delete(key);
  }

  /**
   * Invalidate all cache entries that match a specific pattern
   * @param pattern - The pattern to match (substring of the key)
   */
  invalidatePattern(pattern: string): void {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Get or fetch data
   * If data exists in cache and is not expired, return it
   * Otherwise, fetch new data using the provided fetcher function
   * 
   * @param key - The cache key
   * @param fetcher - A function that returns a Promise with the data
   * @param options - Cache options
   * @returns Promise with the data
   */
  async getOrFetch<T>(
    key: string, 
    fetcher: () => Promise<T>, 
    options?: CacheOptions
  ): Promise<T> {
    const cachedData = this.get<T>(key, options);
    
    if (cachedData !== null) {
      return cachedData;
    }
    
    const data = await fetcher();
    this.set(key, data);
    return data;
  }
}

export const cacheService = new CacheService();