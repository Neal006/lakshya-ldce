'use client';

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { ProductChart } from '@/components/charts';
import { apiClient } from '@/lib/api-client';
import { Card, Badge } from '@/components/ui';
import { 
  Package, 
  TrendingDown, 
  TrendingUp, 
  Star, 
  AlertCircle,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';

interface ProductData {
  product_id: string;
  name: string;
  total_complaints: number;
  avg_sentiment: number;
  positive_count: number;
  negative_count: number;
  high_priority_count: number;
  resolution_rate: number;
  sentiment_trend: string;
  top_issues: string[];
}

export default function OperationalDashboard() {
  const [products, setProducts] = useState<ProductData[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await apiClient.getProductAnalytics();
      setProducts(res.products);
    } catch (error) {
      console.error('Failed to fetch product analytics:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex min-h-screen bg-[var(--color-background)] items-center justify-center">
        <div className="text-gray-400">Loading product analytics...</div>
      </div>
    );
  }

  const worstProduct = products.length > 0
    ? products.reduce((prev, current) => prev.total_complaints > current.total_complaints ? prev : current)
    : null;

  const bestProduct = products.length > 0
    ? products.reduce((prev, current) => prev.avg_sentiment > current.avg_sentiment ? prev : current)
    : null;

  return (
    <div className="flex min-h-screen bg-[var(--color-background)]">
      <Sidebar role="operational" />
      
      <main className="flex-1 p-8">
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        >
          <h1 className="text-3xl font-bold text-[var(--color-secondary)]">Product Analytics</h1>
          <p className="text-gray-500 mt-1">Analyze product performance and customer sentiment</p>
        </motion.div>

        {worstProduct && bestProduct && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              <Card className="h-full border-l-4" style={{ borderLeftColor: 'var(--color-status)' }}>
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-red-100">
                    <TrendingDown className="text-[var(--color-status)]" size={24} />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-[var(--color-secondary)] mb-2">Needs Attention</h3>
                    <p className="text-2xl font-bold text-[var(--color-secondary)]">{worstProduct.name}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {worstProduct.total_complaints} complaints · Avg sentiment: {worstProduct.avg_sentiment.toFixed(2)}
                    </p>
                    <div className="flex gap-2 mt-3">
                      <Badge variant="urgent">{worstProduct.high_priority_count} High Priority</Badge>
                      <Badge variant="default">{worstProduct.top_issues[0] || 'Product Issues'}</Badge>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              <Card className="h-full border-l-4" style={{ borderLeftColor: 'var(--color-primary)' }}>
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-green-100">
                    <TrendingUp className="text-[var(--color-primary)]" size={24} />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-[var(--color-secondary)] mb-2">Top Performer</h3>
                    <p className="text-2xl font-bold text-[var(--color-secondary)]">{bestProduct.name}</p>
                    <p className="text-sm text-gray-500 mt-1">
                      {bestProduct.total_complaints} complaints · Avg sentiment: {bestProduct.avg_sentiment.toFixed(2)}
                    </p>
                    <div className="flex gap-2 mt-3">
                      <Badge variant="success">{bestProduct.positive_count} Positive Reviews</Badge>
                      <Badge variant="default">Low Issues</Badge>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          </div>
        )}

        <div className="mb-8">
          <ProductChart data={products.map(p => ({
            ...p,
            positive: p.positive_count,
            negative: p.negative_count,
            high_priority: p.high_priority_count,
          }))} title="Complaints by Product" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
        >
          <h2 className="text-xl font-bold text-[var(--color-secondary)] mb-4">Product Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product, index) => (
              <motion.div
                key={product.product_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index + 0.4 }}
              >
                <Card className="relative overflow-hidden">
                  <div 
                    className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-20 -translate-y-1/2 translate-x-1/2"
                    style={{ 
                      backgroundColor: product.avg_sentiment > -0.2 ? 'var(--color-primary)' : 'var(--color-status)' 
                    }}
                  />
                  
                  <div className="flex items-start gap-3 mb-4">
                    <div className="p-2 rounded-lg bg-gradient-to-br from-[var(--color-background)] to-[var(--color-background-dark)] shadow-md">
                      <Package size={20} className="text-[var(--color-secondary)]" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-[var(--color-secondary)] line-clamp-1">{product.name}</h3>
                      <p className="text-xs text-gray-400">{product.total_complaints} complaints</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="card-pressed p-2 text-center">
                      <div className="flex items-center justify-center gap-1 text-green-600">
                        <ThumbsUp size={14} />
                        <span className="text-sm font-semibold">{product.positive_count}</span>
                      </div>
                      <p className="text-xs text-gray-400">Positive</p>
                    </div>
                    <div className="card-pressed p-2 text-center">
                      <div className="flex items-center justify-center gap-1 text-[var(--color-status)]">
                        <ThumbsDown size={14} />
                        <span className="text-sm font-semibold">{product.negative_count}</span>
                      </div>
                      <p className="text-xs text-gray-400">Negative</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Star size={14} className="text-yellow-500" />
                      <span className="text-sm font-medium">Sentiment: {product.avg_sentiment.toFixed(2)}</span>
                    </div>
                    {product.high_priority_count > 5 && (
                      <Badge variant="urgent" className="text-xs">{product.high_priority_count} High</Badge>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {worstProduct && (
          <motion.div
            className="mt-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <Card className="border-l-4" style={{ borderLeftColor: 'var(--color-accent)' }}>
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-xl bg-purple-100">
                  <AlertCircle className="text-[var(--color-accent)]" size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-[var(--color-secondary)] mb-2">
                    AI-Generated Product Insight
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    Analysis shows that <strong>{worstProduct.name}</strong> has the highest complaint volume 
                    with {worstProduct.total_complaints} cases. Primary issues relate to {worstProduct.top_issues.join(', ') || 'product quality'}. 
                    The negative sentiment score of {worstProduct.avg_sentiment.toFixed(2)} indicates urgent need for quality review. 
                    <strong>Recommendation:</strong> Initiate immediate QA investigation and consider temporary batch hold pending resolution.
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </main>
    </div>
  );
}