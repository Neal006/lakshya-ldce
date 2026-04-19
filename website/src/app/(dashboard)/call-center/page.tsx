'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { Card, Button, Input, Badge } from '@/components/ui';
import { apiClient } from '@/lib/api-client';
import { 
  Mic, 
  Upload, 
  MessageSquare, 
  Send, 
  CheckCircle, 
  Loader2,
  Phone,
  Mail,
  User,
  Package,
  AlertTriangle,
  AlertCircle
} from 'lucide-react';

type Source = 'call' | 'email' | 'walkin';

interface Product {
  id: string;
  name: string;
  sku: string;
}

export default function CallCenterPage() {
  const [source, setSource] = useState<Source>('walkin');
  const [customerName, setCustomerName] = useState('');
  const [customerContact, setCustomerContact] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [complaintText, setComplaintText] = useState('');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const [products, setProducts] = useState<Product[]>([]);
  const [submitResult, setSubmitResult] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    apiClient.getProducts().then(res => setProducts(res.products)).catch(console.error);
  }, []);

  const handleAudioUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioFile(file);
      setIsProcessingAudio(true);
      try {
        const result = await (await import('@/lib/stt-client')).transcribeAudio(file);
        setComplaintText(result.text);
      } catch (err) {
        console.error('STT failed:', err);
        setComplaintText('Audio transcription failed. Please enter complaint manually.');
      } finally {
        setIsProcessingAudio(false);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    setSubmitResult(null);

    try {
      const payload: any = {
        source,
        product_id: selectedProduct,
        customer_name: customerName,
        text: complaintText,
      };

      if (source === 'email') {
        payload.customer_email = customerContact;
      } else {
        payload.customer_phone = customerContact;
      }

      const result = await apiClient.createComplaint(payload);
      setSubmitResult(result);
      setIsSuccess(true);

      setTimeout(() => {
        setIsSuccess(false);
        setCustomerName('');
        setCustomerContact('');
        setSelectedProduct('');
        setComplaintText('');
        setAudioFile(null);
        setSubmitResult(null);
      }, 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to submit complaint');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-[var(--color-background)]">
      <Sidebar role="call_center" />
      
      <main className="flex-1 p-8">
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        >
          <h1 className="text-3xl font-bold text-[var(--color-secondary)]">New Complaint</h1>
          <p className="text-gray-500 mt-1">Record and process customer complaints</p>
        </motion.div>

        <div className="max-w-4xl mx-auto">
          <AnimatePresence mode="wait">
            {isSuccess && submitResult ? (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="card p-12 text-center"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                  className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6"
                >
                  <CheckCircle className="text-green-600" size={40} />
                </motion.div>
                <h2 className="text-2xl font-bold text-[var(--color-secondary)] mb-2">
                  Complaint Submitted!
                </h2>
                <p className="text-gray-500 mb-6">
                  Complaint has been classified and is being processed.
                </p>
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="card-pressed p-4 text-center">
                    <p className="text-sm text-gray-400">Category</p>
                    <p className="text-lg font-bold text-[var(--color-primary)]">{submitResult.category}</p>
                  </div>
                  <div className="card-pressed p-4 text-center">
                    <p className="text-sm text-gray-400">Priority</p>
                    <p className="text-lg font-bold text-[var(--color-status)]">{submitResult.priority}</p>
                  </div>
                  <div className="card-pressed p-4 text-center">
                    <p className="text-sm text-gray-400">Sentiment</p>
                    <p className="text-lg font-bold">{submitResult.sentiment_score.toFixed(2)}</p>
                  </div>
                </div>
                {submitResult.assigned_team && (
                  <p className="text-sm text-gray-500 mt-4">
                    Assigned to: <strong>{submitResult.assigned_team}</strong>
                  </p>
                )}
                {submitResult.escalation_required && (
                  <div className="mt-3 flex items-center justify-center gap-2 text-[var(--color-status)]">
                    <AlertTriangle size={16} />
                    <span className="font-semibold">Escalation Required</span>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.form
                key="form"
                onSubmit={handleSubmit}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              >
                <Card className="p-8">
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mb-6 p-4 rounded-xl bg-red-50 text-red-700 flex items-center gap-2"
                    >
                      <AlertCircle size={20} />
                      <span className="text-sm">{error}</span>
                    </motion.div>
                  )}

                  <div className="mb-8">
                    <label className="block text-sm font-medium text-[var(--color-secondary)] mb-3">
                      Complaint Source
                    </label>
                    <div className="flex gap-3">
                      {([
                        { id: 'call', label: 'Phone Call', icon: Phone },
                        { id: 'email', label: 'Email', icon: Mail },
                        { id: 'walkin', label: 'Walk-in', icon: User },
                      ] as const).map((item) => {
                        const Icon = item.icon;
                        const isSelected = source === item.id;
                        return (
                          <motion.button
                            key={item.id}
                            type="button"
                            onClick={() => setSource(item.id)}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl transition-all ${
                              isSelected 
                                ? 'bg-[var(--color-primary)] text-white shadow-lg' 
                                : 'card-pressed text-gray-600'
                            }`}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <Icon size={18} />
                            <span className="font-medium">{item.label}</span>
                          </motion.button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-secondary)] mb-2">Customer Name</label>
                      <div className="relative">
                        <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                          type="text"
                          value={customerName}
                          onChange={(e) => setCustomerName(e.target.value)}
                          placeholder="Enter customer name"
                          className="input pl-12"
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-secondary)] mb-2">Contact (Email/Phone)</label>
                      <div className="relative">
                        {source === 'email' ? (
                          <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        ) : (
                          <Phone className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        )}
                        <input
                          type="text"
                          value={customerContact}
                          onChange={(e) => setCustomerContact(e.target.value)}
                          placeholder={source === 'email' ? "customer@email.com" : "+1 234 567 8900"}
                          className="input pl-12"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div className="mb-6">
                    <label className="block text-sm font-medium text-[var(--color-secondary)] mb-2">Product</label>
                    <div className="relative">
                      <Package className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                      <select
                        value={selectedProduct}
                        onChange={(e) => setSelectedProduct(e.target.value)}
                        className="input pl-12 appearance-none cursor-pointer"
                        required
                      >
                        <option value="">Select a product...</option>
                        {products.map((product) => (
                          <option key={product.id} value={product.id}>{product.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {source === 'call' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mb-6"
                    >
                      <label className="block text-sm font-medium text-[var(--color-secondary)] mb-2">
                        Call Recording (Optional)
                      </label>
                      <div className="flex gap-3">
                        <motion.button
                          type="button"
                          onClick={() => fileInputRef.current?.click()}
                          className="flex-1 card-pressed py-4 px-6 rounded-xl flex items-center justify-center gap-3 text-gray-600 hover:text-[var(--color-primary)] transition-colors"
                          whileHover={{ scale: 1.01 }}
                          whileTap={{ scale: 0.99 }}
                        >
                          <Upload size={20} />
                          <span>{audioFile ? audioFile.name : 'Upload .wav file'}</span>
                        </motion.button>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".wav,.mp3"
                          onChange={handleAudioUpload}
                          className="hidden"
                        />
                      </div>
                      
                      {isProcessingAudio && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="mt-3 flex items-center gap-2 text-[var(--color-primary)]"
                        >
                          <Loader2 className="animate-spin" size={16} />
                          <span className="text-sm">Transcribing audio...</span>
                        </motion.div>
                      )}
                    </motion.div>
                  )}

                  <div className="mb-8">
                    <label className="block text-sm font-medium text-[var(--color-secondary)] mb-2">
                      Complaint Details
                    </label>
                    <div className="relative">
                      <MessageSquare className="absolute left-4 top-4 text-gray-400" size={18} />
                      <textarea
                        value={complaintText}
                        onChange={(e) => setComplaintText(e.target.value)}
                        placeholder="Describe the customer's complaint..."
                        className="input pl-12 min-h-[120px] resize-none"
                        required
                      />
                    </div>
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full py-4 text-lg"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="animate-spin" size={20} />
                        Processing with AI...
                      </>
                    ) : (
                      <>
                        <Send size={20} />
                        Submit Complaint
                      </>
                    )}
                  </Button>

                  <motion.div 
                    className="mt-6 flex items-start gap-3 p-4 rounded-xl bg-blue-50 text-blue-700"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                  >
                    <AlertTriangle size={20} className="flex-shrink-0 mt-0.5" />
                    <p className="text-sm">
                      This complaint will be automatically classified by AI into category and priority, 
                      and a resolution will be generated for the customer.
                    </p>
                  </motion.div>
                </Card>
              </motion.form>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}