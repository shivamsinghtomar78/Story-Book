import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles, BookOpen } from 'lucide-react';

export default function Hero() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-slate-950 overflow-hidden relative">
            {/* Background Decorative Elements */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
                <img
                    src="/hero-bg.png"
                    alt=""
                    className="absolute w-full h-full object-cover opacity-20 mix-blend-overlay pointer-events-none"
                />
                <div className="absolute -top-20 -left-20 w-96 h-96 bg-purple-600 rounded-full mix-blend-screen filter blur-[100px] opacity-30 animate-blob"></div>
                <div className="absolute top-0 -right-20 w-96 h-96 bg-cyan-600 rounded-full mix-blend-screen filter blur-[100px] opacity-30 animate-blob animation-delay-2000"></div>
                <div className="absolute -bottom-20 left-20 w-96 h-96 bg-pink-600 rounded-full mix-blend-screen filter blur-[100px] opacity-30 animate-blob animation-delay-4000"></div>
            </div>

            {/* Navigation */}
            <nav className="relative z-10 flex justify-between items-center px-6 py-6 max-w-7xl mx-auto">
                <div className="flex items-center space-x-2">
                    <BookOpen className="w-8 h-8 text-cyan-400" />
                    <span className="text-xl font-bold text-white tracking-tight">StoryBook AI</span>
                </div>
                <div className="flex items-center space-x-4">
                    <button
                        onClick={() => navigate('/login')}
                        className="text-slate-300 hover:text-white font-medium px-4 py-2 transition-colors"
                    >
                        Log in
                    </button>
                    <button
                        onClick={() => navigate('/signup')}
                        className="bg-indigo-600 text-white px-5 py-2.5 rounded-full font-medium hover:bg-indigo-500 transition-colors shadow-lg hover:shadow-indigo-500/50"
                    >
                        Sign up
                    </button>
                </div>
            </nav>

            {/* Hero Content */}
            <div className="relative z-10 flex flex-col items-center justify-center pt-20 pb-32 px-4 text-center">
                <motion.div
                    initial="hidden"
                    animate="visible"
                    variants={{
                        hidden: { opacity: 0 },
                        visible: {
                            opacity: 1,
                            transition: {
                                staggerChildren: 0.2
                            }
                        }
                    }}
                    className="max-w-4xl mx-auto"
                >
                    <motion.div
                        variants={{
                            hidden: { opacity: 0, y: 20 },
                            visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100 } }
                        }}
                    >
                        <span className="inline-flex items-center px-4 py-1.5 rounded-full bg-slate-900/50 text-cyan-300 text-sm font-semibold mb-8 border border-slate-800 shadow-sm backdrop-blur-sm cursor-default">
                            <Sparkles className="w-4 h-4 mr-2 text-yellow-400" />
                            AI-Powered Story Generation
                        </span>
                    </motion.div>

                    <motion.h1
                        variants={{
                            hidden: { opacity: 0, y: 30 },
                            visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100 } }
                        }}
                        className="text-6xl md:text-8xl font-extrabold text-white tracking-tight mb-8 leading-tight drop-shadow-lg"
                    >
                        Craft Magical Stories <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 animate-gradient-x">
                            in Seconds
                        </span>
                    </motion.h1>

                    <motion.p
                        variants={{
                            hidden: { opacity: 0, y: 20 },
                            visible: { opacity: 1, y: 0 }
                        }}
                        className="text-xl md:text-2xl text-slate-300 max-w-2xl mx-auto mb-12 leading-relaxed"
                    >
                        Turn your creative ideas into beautifully illustrated children's books.
                        Professional narration, stunning imagery, and engaging plots created instantly.
                    </motion.p>

                    <motion.div
                        variants={{
                            hidden: { opacity: 0, y: 20 },
                            visible: { opacity: 1, y: 0 }
                        }}
                        className="flex flex-col sm:flex-row gap-5 w-full justify-center items-center"
                    >
                        <button
                            onClick={() => navigate('/signup')}
                            className="group flex items-center justify-center bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-4 rounded-full font-bold text-lg hover:from-indigo-500 hover:to-purple-500 transition-all shadow-xl hover:shadow-purple-500/30 hover:-translate-y-1 w-full sm:w-auto"
                        >
                            Start Creating Free
                            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </button>
                        <button
                            onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
                            className="px-8 py-4 rounded-full font-bold text-lg text-white bg-slate-800 border-2 border-slate-700 hover:border-slate-600 hover:bg-slate-700 transition-all w-full sm:w-auto"
                        >
                            How it works
                        </button>
                    </motion.div>
                </motion.div>
            </div>

            {/* Feature Grid (Minimal) */}
            <div id="features" className="relative z-10 max-w-7xl mx-auto px-4 py-24 border-t border-slate-800/50">
                <div className="grid md:grid-cols-3 gap-12">
                    {[
                        { title: "AI Generation", desc: "Advanced LLMs craft unique, coherent stories tailored to your prompt." },
                        { title: "Vibrant Art", desc: "Consistent, high-quality illustrations for every page of your book." },
                        { title: "Audio Narration", desc: "Natural-sounding voiceovers bring your story to life." }
                    ].map((feature, i) => (
                        <div key={i} className="group p-6 rounded-2xl bg-slate-900/50 border border-slate-800 shadow-lg hover:shadow-cyan-900/20 transition-all hover:border-slate-700">
                            <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                            <p className="text-slate-400 leading-relaxed">{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
