import React, { useState } from "react";
import { Eye, EyeOff, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email === "admin" && password === "admin") {
      setError("");
      if (onLogin) onLogin();
    } else {
      setError("Invalid username or password");
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-gradient-to-br from-blue-100 via-blue-50 to-blue-200">
     {/* Floating Blobs */}
      <motion.div
        className="absolute w-96 h-96 bg-blue-300 rounded-full top-10 left-20 opacity-70 blur-3xl"
        animate={{ y: [0, 20, 0], x: [0, 10, 0] }}
        transition={{ duration: 8, repeat: Infinity, repeatType: "mirror" }}
      />
      <motion.div
        className="absolute w-72 h-72 bg-blue-300 rounded-full top-64 right-32 opacity-60 blur-2xl"
        animate={{ y: [0, -15, 0], x: [0, -10, 0] }}
        transition={{ duration: 10, repeat: Infinity, repeatType: "mirror" }}
      />
      <motion.div
        className="absolute w-80 h-80 bg-blue-400 rounded-full bottom-20 left-1/4 opacity-50 blur-3xl"
        animate={{ y: [0, 25, 0], x: [0, -15, 0] }}
        transition={{ duration: 12, repeat: Infinity, repeatType: "mirror" }}
      />
      <motion.div
        className="absolute w-64 h-64 bg-green-300 rounded-full bottom-32 right-1/3 opacity-40 blur-2xl"
        animate={{ y: [0, -20, 0], x: [0, 15, 0] }}
        transition={{ duration: 9, repeat: Infinity, repeatType: "mirror" }}
      />
      {/* Container Box */}
      <div className="w-full max-w-6xl bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden flex">
        
        {/* Left Side - Illustration */}
        <motion.div
          className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-300 to-blue-400 items-center justify-center p-12"
          initial={{ x: -200, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <div className="max-w-md text-center space-y-6">
            {/* Professional HR Images Grid */}
            <motion.div
              className="mb-8 relative"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.8 }}
            >
              <div className="grid grid-cols-2 gap-4 mb-6">
                {/* Team Building */}
                <motion.div
                  className="relative overflow-hidden rounded-2xl shadow-2xl"
                  whileHover={{ scale: 1.05, rotate: 2 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="w-40 h-32 bg-gradient-to-br from-blue-500 to-blue-800 flex items-center justify-center">
                    <div className="text-white text-center">
                      <div className="w-16 h-16 mx-auto mb-2 bg-white/20 rounded-full flex items-center justify-center">
                        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"/>
                        </svg>
                      </div>
                      <p className="text-xs font-medium">Team Building</p>
                    </div>
                  </div>
                </motion.div>

                {/* Analytics */}
                <motion.div
                  className="relative overflow-hidden rounded-2xl shadow-2xl"
                  whileHover={{ scale: 1.05, rotate: -2 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="w-40 h-32 bg-gradient-to-br from-blue-500 to-blue-800 flex items-center justify-center">
                    <div className="text-white text-center">
                      <div className="w-16 h-16 mx-auto mb-2 bg-white/20 rounded-full flex items-center justify-center">
                        <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
                        </svg>
                      </div>
                      <p className="text-xs font-medium">Analytics</p>
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Main Professional Image */}
              <motion.div
                className="relative overflow-hidden rounded-3xl shadow-2xl"
                animate={{ y: [0, -5, 0] }}
                transition={{ repeat: Infinity, duration: 4 }}
              >
                <div className="w-80 h-48 bg-gradient-to-r from-blue-500 via-blue-600 to-indigo-700 flex items-center justify-center relative">
                  <div className="absolute inset-0 bg-black/10"></div>
                  <div className="relative z-10 text-white text-center">
                    <div className="flex justify-center space-x-4 mb-4">
                      <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2h2zm4-3a1 1 0 00-1 1v1h2V4a1 1 0 00-1-1zM4 9v2h2V9H4zm10 0v2h2V9h-2z"/>
                        </svg>
                      </div>
                      <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                      </div>
                      <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                        </svg>
                      </div>
                    </div>
                    <h3 className="text-lg font-bold mb-2">HR Assistant</h3>
                    <p className="text-sm text-blue-100">Streamline your workforce operations</p>
                  </div>
                </div>
              </motion.div>

              {/* Bottom Feature Cards */}
              <div className="grid grid-cols-3 gap-2 mt-4">
                {/* Recruitment */}
                <motion.div className="bg-white/20 backdrop-blur-sm rounded-xl p-3 text-center" whileHover={{ scale: 1.05 }}>
                  <div className="w-8 h-8 bg-white/30 rounded-full mx-auto mb-1 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6z"/>
                    </svg>
                  </div>
                  <p className="text-xs text-white font-medium">Recruitment</p>
                </motion.div>

                {/* Onboarding */}
                <motion.div className="bg-white/20 backdrop-blur-sm rounded-xl p-3 text-center" whileHover={{ scale: 1.05 }}>
                  <div className="w-8 h-8 bg-white/30 rounded-full mx-auto mb-1 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"/>
                    </svg>
                  </div>
                  <p className="text-xs text-white font-medium">Onboarding</p>
                </motion.div>

                {/* Payroll */}
                <motion.div className="bg-white/20 backdrop-blur-sm rounded-xl p-3 text-center" whileHover={{ scale: 1.05 }}>
                  <div className="w-8 h-8 bg-white/30 rounded-full mx-auto mb-1 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
                      <path fillRule="evenodd" d="M4 5a2 2 0 012-2v1a2 2 0 002 2h6a2 2 0 002-2V3a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3z"/>
                    </svg>
                  </div>
                  <p className="text-xs text-white font-medium">Payroll</p>
                </motion.div>
              </div>
            </motion.div>

            <motion.h1 className="text-3xl font-bold text-white mb-3" initial={{ y: 50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.5, duration: 0.8 }}>
              Super HR
            </motion.h1>

            <motion.p className="text-blue-100 text-lg" initial={{ y: 50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.7, duration: 0.8 }}>
              Everything you need in an easily customizable dashboard
            </motion.p>
          </div>
        </motion.div>

        {/* Right Side - Login Form */}
        <motion.div
          className="w-full lg:w-1/2 flex items-center justify-center p-8 relative"
          initial={{ x: 200, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <motion.div
            className="w-full max-w-md bg-white/60 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/40 p-8 sm:p-10 relative z-10"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            {/* Logo */}
            <div className="flex justify-center mb-8">
              <img
                src="/company-logo.jpg"
                alt="VVDN Logo"
                className="w-28 h-auto transform transition-transform duration-500 hover:scale-110"
              />
            </div>

            <h2 className="text-3xl font-bold text-gray-900 text-center mb-2">
              Welcome Back!
            </h2>
            <p className="text-gray-500 text-center mb-8">Please enter your details</p>

            {error && (
              <motion.div
                className="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 text-sm rounded-lg shadow-sm"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                {error}
              </motion.div>
            )}

            <div className="space-y-6">
              {/* Username */}
              <div>
                <label className="block text-gray-700 font-medium mb-2">
                  Username
                </label>
                <motion.input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your username"
                  className="w-full px-4 py-3 border border-gray-200 rounded-lg bg-white/70 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  whileFocus={{ scale: 1.02 }}
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-gray-700 font-medium mb-2">
                  Password
                </label>
                <div className="relative">
                  <motion.input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-lg bg-white/70 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                    whileFocus={{ scale: 1.02 }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-gray-600 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={() => setRememberMe(!rememberMe)}
                    className="w-4 h-4 text-blue-500 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm">Remember me</span>
                </label>
                <button className="text-sm text-blue-600 hover:underline">
                  Forgot Password?
                </button>
              </div>

              {/* Login Button */}
              <motion.button
                onClick={handleSubmit}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white py-3 rounded-lg font-semibold shadow-lg shadow-blue-200 flex items-center justify-center gap-2 transition-all"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                Login
                <ArrowRight className="w-5 h-5" />
              </motion.button>

              {/* Footer */}
              <p className="text-xs text-gray-500 text-center mt-4">
                By creating an account, you agree to our{" "}
                <button className="text-blue-600 hover:underline">
                  Terms of Service
                </button>{" "}
                and{" "}
                <button className="text-blue-600 hover:underline">
                  Privacy Policy
                </button>
              </p>

              <p className="text-sm text-gray-700 text-center font-medium mt-4">
                Powered by <span className="text-blue-600 font-semibold">AI HR Assistant</span>
              </p>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
};

export default Login;
