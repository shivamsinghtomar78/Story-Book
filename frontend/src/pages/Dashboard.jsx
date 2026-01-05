import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wand2, Loader2, Book, Download, Headphones, ArrowLeft, LogOut } from 'lucide-react';
import api from '../api';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
    const [prompt, setPrompt] = useState('');
    const [length, setLength] = useState('normal');
    const [loading, setLoading] = useState(false);
    const [story, setStory] = useState(null);
    const navigate = useNavigate();

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    const handleGenerate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStory(null);
        try {
            const res = await api.post('/generate', { prompt, length });
            setStory(res.data);
        } catch (err) {
            console.error(err);
            alert('Failed to generate story. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 relative">
            {/* Header */}
            <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-6 py-4 flex justify-between items-center sticky top-0 z-40">
                <div className="flex items-center space-x-2">
                    <Book className="w-6 h-6 text-cyan-400" />
                    <span className="font-bold text-white">Dashboard</span>
                </div>
                <button onClick={handleLogout} className="text-slate-400 hover:text-white transition-colors">
                    <LogOut className="w-5 h-5" />
                </button>
            </header>

            <div className="max-w-5xl mx-auto px-4 py-12 relative z-0">
                <AnimatePresence mode="wait">
                    {!story ? (
                        <motion.div
                            key="form"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className="bg-slate-900 rounded-2xl shadow-xl border border-slate-800 p-8 md:p-12 text-center"
                        >
                            <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-6 border border-slate-700">
                                <Wand2 className="w-8 h-8 text-purple-400" />
                            </div>
                            <h2 className="text-3xl font-bold text-white mb-4">What shall we create today?</h2>
                            <p className="text-slate-400 mb-8 max-w-lg mx-auto">
                                Describe your story idea in detail. Include characters, setting, and the adventure.
                            </p>

                            <form onSubmit={handleGenerate} className="max-w-2xl mx-auto space-y-8">
                                <div className="space-y-2 text-left">
                                    <label className="text-sm font-medium text-cyan-400 ml-1">Your Story Prompt</label>
                                    <textarea
                                        value={prompt}
                                        onChange={(e) => setPrompt(e.target.value)}
                                        placeholder="A brave little toaster who wants to see the world..."
                                        rows={4}
                                        required
                                        className="w-full px-6 py-4 rounded-xl bg-slate-800/50 border border-slate-700 text-white placeholder-slate-500 focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all outline-none resize-none text-lg shadow-inner"
                                    />
                                </div>

                                <div className="space-y-2 text-left">
                                    <label className="text-sm font-medium text-purple-400 ml-1">Story Length</label>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        {['short', 'normal', 'long', 'extended'].map((opt) => (
                                            <button
                                                key={opt}
                                                type="button"
                                                onClick={() => setLength(opt)}
                                                className={`py-3 px-2 rounded-xl font-medium border transition-all capitalize text-sm md:text-base
                            ${length === opt
                                                        ? 'bg-purple-900/40 border-purple-500 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.3)]'
                                                        : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-200'}`}
                                            >
                                                {opt}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 text-white py-4 rounded-xl font-bold text-xl hover:from-cyan-500 hover:to-blue-500 transition-all shadow-lg hover:shadow-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center overflow-hidden relative group font-sans tracking-wide"
                                >
                                    <span className="relative z-10 flex items-center">
                                        <Wand2 className="w-6 h-6 mr-3 group-hover:rotate-12 transition-transform" />
                                        Generate Magic Story
                                    </span>
                                </button>
                            </form>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="result"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="space-y-8"
                        >
                            <div className="flex justify-between items-center bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-sm">
                                <button
                                    onClick={() => setStory(null)}
                                    className="flex items-center text-slate-400 hover:text-white font-medium transition-colors"
                                >
                                    <ArrowLeft className="w-5 h-5 mr-2" />
                                    Create New
                                </button>
                                <div className="flex space-x-3">
                                    {story.pdf_url && (
                                        <a
                                            href={story.pdf_url}
                                            target="_blank"
                                            download
                                            className="flex items-center px-4 py-2 bg-indigo-900/30 text-indigo-300 border border-indigo-500/30 rounded-lg font-medium hover:bg-indigo-900/50 transition-colors"
                                        >
                                            <Download className="w-4 h-4 mr-2" />
                                            PDF
                                        </a>
                                    )}
                                    {story.audiobook_url && (
                                        <a
                                            href={story.audiobook_url}
                                            target="_blank"
                                            download
                                            className="flex items-center px-4 py-2 bg-pink-900/30 text-pink-300 border border-pink-500/30 rounded-lg font-medium hover:bg-pink-900/50 transition-colors"
                                        >
                                            <Headphones className="w-4 h-4 mr-2" />
                                            Audiobook
                                        </a>
                                    )}
                                </div>
                            </div>

                            <div className="grid gap-8">
                                <div className="text-center py-8">
                                    <h1 className="text-4xl font-serif font-bold text-white mb-2 drop-shadow-md">{story.story_data.title}</h1>
                                    {story.story_data.moral && (
                                        <p className="text-cyan-300 italic">"{story.story_data.moral}"</p>
                                    )}
                                </div>

                                {story.story_data.pages.map((page, index) => (
                                    <motion.div
                                        initial={{ opacity: 0, y: 30 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        key={index}
                                        className="bg-slate-900 p-6 md:p-8 rounded-2xl shadow-xl border border-slate-800 flex flex-col md:flex-row gap-8 items-center hover:shadow-2xl hover:shadow-purple-900/10 transition-shadow"
                                    >
                                        <div className="w-full md:w-1/2 aspect-[4/3] bg-slate-800 rounded-xl overflow-hidden shadow-inner relative group border border-slate-700">
                                            <img
                                                src={`/api/download/page_${page.page}_${story.story_id}.png`}
                                                alt={`Page ${page.page}`}
                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                                                onError={(e) => {
                                                    e.target.onerror = null;
                                                    e.target.src = "https://placehold.co/600x400/1e293b/cbd5e1?text=Illustration+Generating...";
                                                }}
                                            />
                                        </div>
                                        <div className="w-full md:w-1/2 flex flex-col justify-between">
                                            <div className="text-lg leading-relaxed text-slate-300 font-serif mb-6">
                                                <p>{page.text}</p>
                                            </div>

                                            <div className="mt-auto">
                                                <div className="bg-slate-800 rounded-lg p-3 mb-4 border border-slate-700">
                                                    <div className="flex items-center gap-3 text-cyan-300 text-sm font-medium mb-2">
                                                        <Headphones className="w-4 h-4" />
                                                        Listen to this page
                                                    </div>
                                                    <audio
                                                        controls
                                                        className="w-full h-8 accent-purple-500"
                                                        src={`/api/download/page_${page.page}_${story.story_id}.mp3`}
                                                    >
                                                        Your browser does not support the audio element.
                                                    </audio>
                                                </div>
                                                <span className="text-xs text-slate-500 block font-sans uppercase tracking-wider">Page {page.page}</span>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Loading Overlay */}
            <AnimatePresence>
                {loading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950/90 backdrop-blur-sm"
                    >
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                            className="w-20 h-20 border-4 border-indigo-900 border-t-cyan-400 rounded-full mb-8 shadow-2xl shadow-cyan-500/20"
                        />
                        <motion.h3
                            animate={{ opacity: [0.5, 1, 0.5] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className="text-3xl font-bold text-white mb-4"
                        >
                            Weaving your story...
                        </motion.h3>
                        <p className="text-slate-400 max-w-md text-center text-lg px-4">
                            Our AI storytellers are crafting the plot, illustrating scenes, and preparing the narration.
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
