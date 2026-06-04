"use client"

import * as React from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { GlassButton } from "@/components/ui/glass-button"
import { UploadCloud, X, FileText, CheckCircle, AlertCircle } from "lucide-react"

interface UploadZoneProps {
    onUploadComplete?: () => void
}

export function UploadZone({ onUploadComplete }: UploadZoneProps) {
    const [selectedFiles, setSelectedFiles] = React.useState<File[]>([])
    const [isDragging, setIsDragging] = React.useState(false)
    const [isUploading, setIsUploading] = React.useState(false)
    const [uploadProgress, setUploadProgress] = React.useState(0)
    const [uploadStatus, setUploadStatus] = React.useState<'idle' | 'success' | 'error'>('idle')
    const [errorMessage, setErrorMessage] = React.useState('')
    const fileInputRef = React.useRef<HTMLInputElement>(null)

    const validateFile = (file: File): boolean => {
        // Check if PDF
        if (file.type !== 'application/pdf') {
            setErrorMessage(`${file.name} is not a PDF file`)
            setUploadStatus('error')
            return false
        }

        // Check size (max 50MB)
        const maxSize = 50 * 1024 * 1024 // 50MB
        if (file.size > maxSize) {
            setErrorMessage(`${file.name} is too large (max 50MB)`)
            setUploadStatus('error')
            return false
        }

        return true
    }

    const handleFileSelect = (files: FileList | null) => {
        if (!files) return

        const validFiles: File[] = []
        Array.from(files).forEach(file => {
            if (validateFile(file)) {
                validFiles.push(file)
            }
        })

        if (validFiles.length > 0) {
            setSelectedFiles(prev => [...prev, ...validFiles])
            setUploadStatus('idle')
            setErrorMessage('')
        }
    }

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)
        handleFileSelect(e.dataTransfer.files)
    }

    const removeFile = (index: number) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index))
    }

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return

        setIsUploading(true)
        setUploadProgress(0)
        setUploadStatus('idle')

        try {
            const formData = new FormData()
            selectedFiles.forEach(file => {
                formData.append('files', file)
            })

            // Simulate progress (since we don't have real progress from fetch)
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval)
                        return 90
                    }
                    return prev + 10
                })
            }, 200)

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/upload`, {
                method: 'POST',
                body: formData,
            })

            clearInterval(progressInterval)
            setUploadProgress(100)

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`)
            }

            const result = await response.json()

            setUploadStatus('success')
            setSelectedFiles([])

            // Call callback if provided
            if (onUploadComplete) {
                onUploadComplete()
            }

            // Reset after 3 seconds
            setTimeout(() => {
                setUploadStatus('idle')
                setUploadProgress(0)
            }, 3000)

        } catch (error) {
            console.error('Upload error:', error)
            setUploadStatus('error')
            setErrorMessage(error instanceof Error ? error.message : 'Upload failed')
        } finally {
            setIsUploading(false)
        }
    }

    return (
        <GlassCard className="p-6 space-y-4">
            {/* Upload Zone */}
            <div
                className={`
                    flex flex-col justify-center items-center text-center space-y-4 
                    border-dashed border-2 rounded-xl p-8 transition-all cursor-pointer
                    ${isDragging
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-white/20 hover:border-blue-500/50 hover:bg-white/5'
                    }
                `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <div className={`p-4 rounded-full transition-colors ${isDragging ? 'bg-blue-500/20' : 'bg-blue-500/10'
                    }`}>
                    <UploadCloud className="w-10 h-10 text-blue-400" />
                </div>
                <div>
                    <h3 className="text-lg font-semibold text-white">Upload Documents</h3>
                    <p className="text-sm text-slate-400 mt-1">
                        Drag & drop PDF files here or click to browse
                    </p>
                    <p className="text-xs text-slate-500 mt-2">
                        Maximum file size: 50MB
                    </p>
                </div>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,application/pdf"
                    multiple
                    className="hidden"
                    onChange={(e) => handleFileSelect(e.target.files)}
                />
            </div>

            {/* Selected Files */}
            {selectedFiles.length > 0 && (
                <div className="space-y-2">
                    <h4 className="text-sm font-medium text-slate-300">
                        Selected Files ({selectedFiles.length})
                    </h4>
                    <div className="space-y-2">
                        {selectedFiles.map((file, index) => (
                            <div
                                key={index}
                                className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10"
                            >
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-white truncate">{file.name}</p>
                                        <p className="text-xs text-slate-400">
                                            {(file.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        removeFile(index)
                                    }}
                                    className="p-1 hover:bg-red-500/10 rounded text-slate-400 hover:text-red-400 transition-colors flex-shrink-0"
                                    disabled={isUploading}
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Upload Progress */}
            {isUploading && (
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="text-slate-300">Uploading...</span>
                        <span className="text-blue-400">{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                        <div
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-full transition-all duration-300"
                            style={{ width: `${uploadProgress}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Status Messages */}
            {uploadStatus === 'success' && (
                <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    <p className="text-sm text-green-400">
                        Documents uploaded and processed successfully!
                    </p>
                </div>
            )}

            {uploadStatus === 'error' && (
                <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <AlertCircle className="w-5 h-5 text-red-400" />
                    <p className="text-sm text-red-400">{errorMessage}</p>
                </div>
            )}

            {/* Upload Button */}
            {selectedFiles.length > 0 && !isUploading && uploadStatus !== 'success' && (
                <GlassButton
                    onClick={handleUpload}
                    className="w-full"
                    disabled={isUploading}
                >
                    Upload {selectedFiles.length} {selectedFiles.length === 1 ? 'File' : 'Files'}
                </GlassButton>
            )}
        </GlassCard>
    )
}
