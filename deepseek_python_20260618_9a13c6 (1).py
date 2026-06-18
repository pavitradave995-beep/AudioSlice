"""
AudioSlice UI Components
Reusable UI components for the application
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
from src.audio_processor import AudioProcessor
from src.utils import format_time, validate_audio_file
from src.project_manager import ProjectManager

def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.markdown("### 🎵 AudioSlice")
        st.markdown("---")
        
        # Navigation
        pages = {
            "🏠 Home": "/",
            "✂️ Editor": "/Editor",
            "🤖 AI Suggestions": "/AI_Suggestions",
            "💾 Projects": "/Projects",
            "⚙️ Settings": "/Settings",
            "ℹ️ About": "/About"
        }
        
        for page_name, page_path in pages.items():
            if st.button(page_name, use_container_width=True, key=page_path):
                st.switch_page(page_path)
        
        st.markdown("---")
        
        # Quick stats
        if st.session_state.audio_file:
            st.caption(f"Current File: {st.session_state.audio_file['name']}")
            st.caption(f"Clips: {len(st.session_state.clips)}")
        else:
            st.caption("No audio loaded")
        
        st.markdown("---")
        st.caption("v1.0.0")

def render_audio_player(audio_data: Dict):
    """
    Render built-in audio player
    
    Args:
        audio_data: Audio data dictionary
    """
    try:
        # Convert audio to bytes for display
        audio_segment = audio_data['audio_segment']
        
        # Export to temporary file for streaming
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            audio_segment.export(tmp_file.name, format='mp3')
            audio_bytes = open(tmp_file.name, 'rb').read()
        
        # Display audio player
        st.audio(audio_bytes, format='audio/mp3')
        
        # Player controls in Streamlit
        st.caption("Play/Pause and seek using the player controls above")
        
    except Exception as e:
        st.error(f"Error loading audio player: {str(e)}")

def render_waveform(audio_data: Dict, height: int = 200):
    """
    Render interactive waveform visualization
    
    Args:
        audio_data: Audio data dictionary
        height: Height of the waveform
    """
    try:
        # Get waveform data
        processor = AudioProcessor()
        waveform = processor.get_waveform_data(
            audio_data, 
            sensitivity=st.session_state.get('waveform_sensitivity', 1.0)
        )
        
        if len(waveform) == 0:
            st.warning("No waveform data available")
            return
        
        # Create time array
        duration = audio_data['duration']
        time = np.linspace(0, duration, len(waveform))
        
        # Create figure
        fig = go.Figure()
        
        # Add waveform trace
        fig.add_trace(go.Scatter(
            x=time,
            y=waveform,
            mode='lines',
            line=dict(color='#00ff88', width=2),
            name='Waveform',
            fill='tozeroy',
            fillcolor='rgba(0, 255, 136, 0.1)'
        ))
        
        # Add clip markers if available
        for clip in st.session_state.get('clips', []):
            fig.add_vrect(
                x0=clip['start'],
                x1=clip['end'],
                fillcolor='rgba(255, 0, 0, 0.2)',
                layer='below',
                line_width=0,
                annotation_text=f"Clip {clip['id']}",
                annotation_position='top'
            )
        
        # Update layout
        fig.update_layout(
            height=height,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title='Time (seconds)',
            yaxis_title='Amplitude',
            xaxis=dict(range=[0, duration]),
            yaxis=dict(range=[-1.2, 1.2]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        # Display figure
        st.plotly_chart(fig, use_container_width=True)
        
        # Zoom controls
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔍 Zoom In"):
                # Zoom in by reducing x-axis range
                pass  # Implement zoom functionality
        with col2:
            if st.button("🔍 Zoom Out"):
                # Zoom out by increasing x-axis range
                pass
        with col3:
            if st.button("⟲ Reset View"):
                # Reset to full view
                pass
        
    except Exception as e:
        st.error(f"Error rendering waveform: {str(e)}")

def render_clip_table(clips: List[Dict]):
    """
    Render table of clips
    
    Args:
        clips: List of clip dictionaries
    """
    if not clips:
        st.info("No clips created yet")
        return
    
    # Create table data
    table_data = []
    for clip in clips:
        table_data.append({
            'Clip #': clip['id'],
            'Start': format_time(clip['start']),
            'End': format_time(clip['end']),
            'Duration': format_time(clip['duration'])
        })
    
    # Display table
    st.table(table_data)

def render_export_section(audio_data: Dict):
    """
    Render export section
    
    Args:
        audio_data: Audio data dictionary
    """
    st.subheader("📤 Merge and Export")
    
    if not st.session_state.clips:
        st.info("No clips to export. Create some clips first!")
        return
    
    # Merge clips
    if st.button("🔄 Merge Clips", use_container_width=True, type="primary"):
        with st.spinner("Merging clips..."):
            try:
                processor = AudioProcessor()
                clips = []
                
                # Extract all clips
                for clip_info in st.session_state.clips:
                    clip = processor.extract_clip(
                        audio_data,
                        clip_info['start'],
                        clip_info['end']
                    )
                    if clip:
                        clips.append(clip)
                
                if clips:
                    # Merge clips
                    merged = processor.merge_clips(clips)
                    
                    if merged:
                        st.session_state.merged_audio = merged
                        st.success(f"✅ Successfully merged {len(clips)} clips!")
                        
                        # Preview merged audio
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                            merged.export(tmp_file.name, format='mp3')
                            st.audio(tmp_file.name, format='audio/mp3')
                else:
                    st.error("Failed to extract clips")
                    
            except Exception as e:
                st.error(f"Error merging clips: {str(e)}")
    
    # Export section
    if 'merged_audio' in st.session_state:
        st.subheader("💾 Export Merged Audio")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                options=['mp3', 'wav']
            )
        
        with col2:
            if export_format == 'mp3':
                bitrate = st.selectbox(
                    "Bitrate",
                    options=['128k', '192k', '256k', '320k']
                )
            else:
                bitrate = None
        
        if st.button("⬇️ Download", use_container_width=True, type="primary"):
            try:
                processor = AudioProcessor()
                export_path = processor.export_audio(
                    st.session_state.merged_audio,
                    export_format,
                    bitrate
                )
                
                if export_path:
                    # Read exported file
                    with open(export_path, 'rb') as f:
                        audio_bytes = f.read()
                    
                    st.download_button(
                        label="⬇️ Download Audio File",
                        data=audio_bytes,
                        file_name=f"merged_audio.{export_format}",
                        mime=f"audio/{export_format}",
                        use_container_width=True
                    )
                    
                    st.success("✅ Audio exported successfully!")
                    
            except Exception as e:
                st.error(f"Error exporting audio: {str(e)}")

def render_save_project_button():
    """Render save project button"""
    st.subheader("💾 Save Project")
    
    project_name = st.text_input("Project Name", value="My Audio Project")
    
    if st.button("💾 Save Project", use_container_width=True):
        try:
            project_data = {
                'name': project_name,
                'audio_file': st.session_state.audio_file,
                'clips': st.session_state.clips,
                'settings': {
                    'export_format': st.session_state.get('export_format', 'mp3'),
                    'waveform_sensitivity': st.session_state.get('waveform_sensitivity', 1.0)
                }
            }
            
            project_manager = ProjectManager()
            file_path = project_manager.save_project(project_data)
            
            st.success(f"✅ Project saved: {file_path}")
            
        except Exception as e:
            st.error(f"Error saving project: {str(e)}")